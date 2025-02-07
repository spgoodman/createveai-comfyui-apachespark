"""
Feature extraction and analysis nodes for ComfyUI
"""

from typing import Optional, Dict, List, Any, Tuple
import numpy as np
from PIL import Image
import io
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType

from .base import Node, SparkConfig, NodeOutput, ValidationError, DataType
from .connection import SessionContext
from .dataset import Dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FeatureExtractionConfig:
    """Configuration for feature extraction"""
    batch_size: int = 32
    cache_results: bool = True
    use_gpu: bool = False
    timeout: int = 300  # seconds

class TextFeatureExtractorNode(Node):
    """Node for extracting features from text data"""
    
    RETURN_TYPES = (DataType.TENSOR, DataType.DICT, DataType.LIST)
    RETURN_NAMES = ("features", "metadata", "prompt_suggestions")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "dataset": (DataType.DATASET, {}),
                "text_column": ("STRING", {}),
                "extraction_type": (
                    ["SEMANTIC_VECTORS", "KEYWORDS", "ENTITIES", "SENTIMENT", "TOPICS"],
                    {"default": "SEMANTIC_VECTORS"}
                )
            },
            "optional": {
                "model_config": ("DICT", {
                    "default": {
                        "model_name": "all-MiniLM-L6-v2",
                        "max_length": 512
                    }
                }),
                "feature_config": ("DICT", {
                    "default": {
                        "batch_size": 32,
                        "cache_results": True
                    }
                })
            }
        }

    def validate_inputs(self, dataset: Dataset, text_column: str) -> None:
        """Validate input parameters"""
        if not isinstance(dataset, Dataset):
            raise ValidationError("Input must be a Dataset instance")
        
        if text_column not in dataset.data.columns:
            raise ValidationError(f"Column '{text_column}' not found in dataset")
        
        # Check if column contains text data
        sample = dataset.data.select(text_column).first()
        if sample and not isinstance(sample[0], str):
            raise ValidationError(f"Column '{text_column}' must contain text data")

    def _extract_semantic_vectors(self,
                                texts: List[str],
                                model_config: Dict,
                                feature_config: Dict) -> np.ndarray:
        """Extract semantic vectors using transformer models"""
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            device = "cuda" if torch.cuda.is_available() and feature_config.get("use_gpu", False) else "cpu"
            model = SentenceTransformer(model_config["model_name"]).to(device)
            
            batch_size = feature_config.get("batch_size", 32)
            vectors = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_vectors = model.encode(
                    batch,
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                vectors.append(batch_vectors)
            
            return np.vstack(vectors)
            
        except ImportError:
            raise ValidationError(
                "sentence-transformers package required for semantic vectors"
            )
        except Exception as e:
            logger.error(f"Error in semantic vector extraction: {str(e)}")
            raise ValidationError(f"Failed to extract semantic vectors: {str(e)}")

    def _extract_keywords(self,
                         texts: List[str],
                         model_config: Dict,
                         feature_config: Dict) -> List[Dict]:
        """Extract keywords from texts"""
        try:
            import yake
            
            kw_extractor = yake.KeywordExtractor(
                lan="en",
                n=3,
                dedupLim=0.3,
                top=10,
                features=None
            )
            
            results = []
            for text in texts:
                try:
                    keywords = kw_extractor.extract_keywords(text)
                    results.append({
                        "keywords": [kw for kw, _ in keywords],
                        "scores": [float(score) for _, score in keywords]
                    })
                except Exception as e:
                    logger.warning(f"Error extracting keywords from text: {str(e)}")
                    results.append({"keywords": [], "scores": []})
            
            return results
            
        except ImportError:
            raise ValidationError("yake package required for keyword extraction")

    def _extract_entities(self,
                         texts: List[str],
                         model_config: Dict,
                         feature_config: Dict) -> List[Dict]:
        """Extract named entities from texts"""
        try:
            import spacy
            
            try:
                nlp = spacy.load("en_core_web_sm")
            except OSError:
                raise ValidationError(
                    "Spacy model not found. Install with: python -m spacy download en_core_web_sm"
                )
            
            results = []
            batch_size = feature_config.get("batch_size", 32)
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                docs = list(nlp.pipe(batch))
                
                for doc in docs:
                    entities = [{
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    } for ent in doc.ents]
                    results.append(entities)
            
            return results
            
        except ImportError:
            raise ValidationError("spacy package required for entity extraction")

    def _analyze_sentiment(self,
                          texts: List[str],
                          model_config: Dict) -> List[Dict]:
        """Analyze sentiment in texts"""
        try:
            from textblob import TextBlob
            results = []
            for text in texts:
                blob = TextBlob(text)
                results.append({
                    "polarity": blob.sentiment.polarity,
                    "subjectivity": blob.sentiment.subjectivity
                })
            return results
        except ImportError:
            raise ValidationError("textblob package required for sentiment analysis")

    def _extract_topics(self,
                       texts: List[str],
                       model_config: Dict) -> Dict:
        """Extract topics from texts"""
        try:
            from gensim import corpora, models
            from gensim.utils import simple_preprocess
            
            processed_texts = [simple_preprocess(text) for text in texts]
            dictionary = corpora.Dictionary(processed_texts)
            corpus = [dictionary.doc2bow(text) for text in processed_texts]
            
            lda_model = models.LdaModel(
                corpus,
                num_topics=5,
                id2word=dictionary
            )
            
            topics = {}
            for idx, topic in lda_model.print_topics(-1):
                topics[f"topic_{idx}"] = topic
                
            return topics
        except ImportError:
            raise ValidationError("gensim package required for topic extraction")

    def _generate_prompt_suggestions(self,
                                   features: Any,
                                   extraction_type: str) -> List[str]:
        """Generate prompt suggestions based on extracted features"""
        suggestions = []
        
        if extraction_type == "KEYWORDS":
            for result in features:
                keywords = result["keywords"][:3]
                suggestions.append(f"Create content focusing on: {', '.join(keywords)}")
                
        elif extraction_type == "ENTITIES":
            entity_types = set()
            for entities in features:
                for entity in entities:
                    entity_types.add(entity["label"])
            for etype in entity_types:
                suggestions.append(f"Include {etype.lower()} elements in the generation")
                
        elif extraction_type == "SENTIMENT":
            avg_polarity = np.mean([r["polarity"] for r in features])
            if avg_polarity > 0.3:
                suggestions.append("Maintain a positive and uplifting tone")
            elif avg_polarity < -0.3:
                suggestions.append("Consider a more serious or dramatic tone")
                
        elif extraction_type == "TOPICS":
            for topic_id, topic_terms in features.items():
                suggestions.append(f"Incorporate theme: {topic_terms}")
        
        return suggestions

    def execute(self,
                dataset: Dataset,
                text_column: str,
                extraction_type: str,
                model_config: Optional[Dict] = None,
                feature_config: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        self.validate_inputs(dataset, text_column)
        
        model_config = model_config or {
            "model_name": "all-MiniLM-L6-v2",
            "max_length": 512
        }
        feature_config = feature_config or {
            "batch_size": 32,
            "cache_results": True
        }
        
        start_time = time.time()
        
        try:
            texts = [row[text_column] for row in dataset.data.collect()]
            
            if extraction_type == "SEMANTIC_VECTORS":
                features = self._extract_semantic_vectors(texts, model_config, feature_config)
                metadata = {
                    "shape": features.shape,
                    "model": model_config["model_name"]
                }
            elif extraction_type == "KEYWORDS":
                features = self._extract_keywords(texts, model_config, feature_config)
                metadata = {
                    "num_texts": len(texts),
                    "max_keywords": 10
                }
            elif extraction_type == "ENTITIES":
                features = self._extract_entities(texts, model_config, feature_config)
                metadata = {"num_texts": len(texts)}
            elif extraction_type == "SENTIMENT":
                features = self._analyze_sentiment(texts, model_config)
                metadata = {"num_texts": len(texts)}
            elif extraction_type == "TOPICS":
                features = self._extract_topics(texts, model_config)
                metadata = {"num_topics": len(features)}
            else:
                raise ValidationError(f"Unsupported extraction type: {extraction_type}")
            
            prompt_suggestions = self._generate_prompt_suggestions(
                features,
                extraction_type
            )
            
            metadata["processing_time"] = time.time() - start_time
            
            return (features, metadata, prompt_suggestions)
            
        except Exception as e:
            logger.error(f"Error in text feature extraction: {str(e)}")
            raise ValidationError(f"Failed to extract text features: {str(e)}")

class ImageFeatureAnalyzerNode(Node):
    """Node for analyzing image features"""
    
    RETURN_TYPES = (DataType.TENSOR, DataType.TENSOR, DataType.DICT)
    RETURN_NAMES = ("visual_features", "style_vectors", "suggested_params")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "dataset": (DataType.DATASET, {}),
                "image_column": ("STRING", {}),
                "analysis_types": (
                    ["COMPOSITION", "COLOR_PALETTE", "OBJECTS", "STYLE", "AESTHETICS"],
                    {"default": ["COMPOSITION", "STYLE"]}
                )
            },
            "optional": {
                "model_config": ("DICT", {"default": {}}),
                "feature_config": ("DICT", {
                    "default": {
                        "batch_size": 16,
                        "cache_results": True,
                        "use_gpu": True
                    }
                })
            }
        }

    def validate_inputs(self, dataset: Dataset, image_column: str) -> None:
        """Validate input parameters"""
        if not isinstance(dataset, Dataset):
            raise ValidationError("Input must be a Dataset instance")
        
        if image_column not in dataset.data.columns:
            raise ValidationError(f"Column '{image_column}' not found in dataset")

    def _analyze_composition(self, image: Image.Image) -> Dict:
        """Analyze image composition"""
        try:
            width, height = image.size
            aspect_ratio = width / height
            
            gray_image = image.convert("L")
            gray_array = np.array(gray_image)
            
            from scipy import ndimage
            edges_x = ndimage.sobel(gray_array, axis=0)
            edges_y = ndimage.sobel(gray_array, axis=1)
            edges = np.hypot(edges_x, edges_y)
            
            brightness_map = np.array(image.convert("L"))
            focal_point = np.unravel_index(
                np.argmax(brightness_map),
                brightness_map.shape
            )
            
            return {
                "aspect_ratio": aspect_ratio,
                "dimensions": (width, height),
                "orientation": "landscape" if width > height else "portrait",
                "edge_density": float(np.mean(edges)),
                "focal_point": {
                    "x": float(focal_point[1] / width),
                    "y": float(focal_point[0] / height)
                }
            }
        except Exception as e:
            logger.error(f"Error in composition analysis: {str(e)}")
            return {
                "aspect_ratio": 1.0,
                "dimensions": (0, 0),
                "orientation": "unknown",
                "edge_density": 0.0,
                "focal_point": {"x": 0.5, "y": 0.5}
            }

    def _extract_color_palette(self, image: Image.Image, num_colors: int = 5) -> Dict:
        """Extract dominant color palette"""
        try:
            image = image.resize((150, 150))
            pixels = np.float32(image).reshape(-1, 3)
            
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=num_colors, n_init=3)
            kmeans.fit(pixels)
            colors = kmeans.cluster_centers_
            
            hex_colors = ['#{:02x}{:02x}{:02x}'.format(
                int(c[0]), int(c[1]), int(c[2])
            ) for c in colors]
            
            color_stats = {
                "mean_rgb": np.mean(pixels, axis=0).tolist(),
                "std_rgb": np.std(pixels, axis=0).tolist(),
                "color_diversity": float(np.std(kmeans.labels_))
            }
            
            return {
                "dominant_colors": hex_colors,
                "color_weights": kmeans.labels_.tolist(),
                "statistics": color_stats
            }
        except Exception as e:
            logger.error(f"Error in color palette extraction: {str(e)}")
            return {
                "dominant_colors": ["#000000"] * num_colors,
                "color_weights": [0] * num_colors,
                "statistics": {
                    "mean_rgb": [0, 0, 0],
                    "std_rgb": [0, 0, 0],
                    "color_diversity": 0.0
                }
            }

    def _detect_objects(self, image: Image.Image) -> Dict:
        """Detect objects in image"""
        try:
            import torch
            import torchvision
            from torchvision.transforms import functional as F
            
            model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
            model.eval()
            
            img_tensor = F.to_tensor(image).unsqueeze(0)
            
            with torch.no_grad():
                predictions = model(img_tensor)
            
            return {
                "boxes": predictions[0]["boxes"].tolist(),
                "labels": predictions[0]["labels"].tolist(),
                "scores": predictions[0]["scores"].tolist()
            }
        except Exception as e:
            logger.error(f"Error in object detection: {str(e)}")
            return {
                "boxes": [],
                "labels": [],
                "scores": []
            }

    def _analyze_style(self, image: Image.Image) -> Dict:
        """Analyze image style"""
        try:
            img_array = np.array(image)
            
            # Basic statistics
            brightness = np.mean(img_array)
            contrast = np.std(img_array)
            
            # Color statistics
            if len(img_array.shape) == 3:
                saturation = np.mean(np.std(img_array, axis=2))
                color_variance = np.var(img_array, axis=(0,1))
            else:
                saturation = 0
                color_variance = np.array([0,0,0])
            
            # Texture analysis
            from skimage.feature import graycomatrix, graycoprops
            gray = np.array(image.convert('L'))
            glcm = graycomatrix(gray, [1], [0], 256, symmetric=True, normed=True)
            contrast = graycoprops(glcm, 'contrast')[0, 0]
            energy = graycoprops(glcm, 'energy')[0, 0]
            homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
            
            return {
                "brightness": float(brightness),
                "contrast": float(contrast),
                "saturation": float(saturation),
                "color_variance": color_variance.tolist(),
                "texture": {
                    "contrast": float(contrast),
                    "energy": float(energy),
                    "homogeneity": float(homogeneity)
                }
            }
        except Exception as e:
            logger.error(f"Error in style analysis: {str(e)}")
            return {
                "brightness": 0.0,
                "contrast": 0.0,
                "saturation": 0.0,
                "color_variance": [0, 0, 0],
                "texture": {
                    "contrast": 0.0,
                    "energy": 0.0,
                    "homogeneity": 0.0
                }
            }

    def _analyze_aesthetics(self, image: Image.Image) -> Dict:
        """Analyze image aesthetics"""
        try:
            import torch
            from torchvision.transforms import functional as F
            
            class AestheticScorer(torch.nn.Module):
                def forward(self, x):
                    features = torch.nn.functional.adaptive_avg_pool2d(x, (1, 1))
                    return torch.mean(features)
            
            model = AestheticScorer()
            img_tensor = F.to_tensor(image).unsqueeze(0)
            
            with torch.no_grad():
                score = model(img_tensor).item()
            
            gray = np.array(image.convert('L'))
            sharpness = float(np.std(gray))
            complexity = float(np.mean(np.abs(np.diff(gray))))
            
            return {
                "aesthetic_score": score,
                "quality_metrics": {
                    "sharpness": sharpness,
                    "complexity": complexity
                }
            }
        except Exception as e:
            logger.error(f"Error in aesthetic analysis: {str(e)}")
            return {
                "aesthetic_score": 0.0,
                "quality_metrics": {
                    "sharpness": 0.0,
                    "complexity": 0.0
                }
            }

    def _generate_suggested_params(self, analysis_results: Dict) -> Dict:
        """Generate suggested parameters for image generation"""
        suggestions = {
            "composition": {
                "aspect_ratio": analysis_results.get("composition", {}).get("aspect_ratio", 1.0),
                "orientation": analysis_results.get("composition", {}).get("orientation", "square")
            },
            "style": {
                "brightness": analysis_results.get("style", {}).get("brightness", 0.5),
                "contrast": analysis_results.get("style", {}).get("contrast", 0.5),
                "saturation": analysis_results.get("style", {}).get("saturation", 0.5)
            },
            "colors": {
                "palette": analysis_results.get("colors", {}).get("dominant_colors", [])
            }
        }
        
        if "aesthetics" in analysis_results:
            suggestions["quality"] = {
                "target_score": analysis_results["aesthetics"]["aesthetic_score"],
                "sharpness": analysis_results["aesthetics"]["quality_metrics"]["sharpness"]
            }
        
        return suggestions

    def execute(self,
                dataset: Dataset,
                image_column: str,
                analysis_types: List[str],
                model_config: Optional[Dict] = None,
                feature_config: Optional[Dict] = None) -> tuple:
        """Execute node functionality"""
        self.validate_inputs(dataset, image_column)
        
        feature_config = feature_config or {
            "batch_size": 16,
            "cache_results": True,
            "use_gpu": True
        }
        
        start_time = time.time()
        
        try:
            # Get images from dataset
            images = []
            for row in dataset.data.collect():
                img_data = row[image_column]
                if isinstance(img_data, (str, bytes)):
                    img = Image.open(io.BytesIO(img_data) if isinstance(img_data, bytes) else img_data)
                else:
                    img = img_data
                images.append(img)
            
            # Process each image
            analysis_results = []
            for img in images:
                image_analysis = {}
                
                if "COMPOSITION" in analysis_types:
                    image_analysis["composition"] = self._analyze_composition(img)
                
                if "COLOR_PALETTE" in analysis_types:
                    image_analysis["colors"] = self._extract_color_palette(img)
                
                if "OBJECTS" in analysis_types:
                    image_analysis["objects"] = self._detect_objects(img)
                
                if "STYLE" in analysis_types:
                    image_analysis["style"] = self._analyze_style(img)
                
                if "AESTHETICS" in analysis_types:
                    image_analysis["aesthetics"] = self._analyze_aesthetics(img)
                
                analysis_results.append(image_analysis)
            
            # Extract features for visual_features tensor
            visual_features = []
            for result in analysis_results:
                features = []
                
                if "composition" in result:
                    features.extend([
                        result["composition"]["aspect_ratio"],
                        result["composition"]["edge_density"]
                    ])
                
                if "style" in result:
                    features.extend([
                        result["style"]["brightness"],
                        result["style"]["contrast"],
                        result["style"]["saturation"]
                    ])
                    features.extend(result["style"]["color_variance"])
                
                if "aesthetics" in result:
                    features.extend([
                        result["aesthetics"]["aesthetic_score"],
                        result["aesthetics"]["quality_metrics"]["sharpness"],
                        result["aesthetics"]["quality_metrics"]["complexity"]
                    ])
                
                visual_features.append(features)
            
            visual_features = np.array(visual_features, dtype=np.float32)
            
            # Extract style vectors
            style_vectors = []
            for result in analysis_results:
                if "style" in result:
                    style_vector = [
                        result["style"]["brightness"],
                        result["style"]["contrast"],
                        result["style"]["saturation"],
                        result["style"]["texture"]["contrast"],
                        result["style"]["texture"]["energy"],
                        result["style"]["texture"]["homogeneity"]
                    ]
                    style_vectors.append(style_vector)
            
            style_vectors = np.array(style_vectors, dtype=np.float32)
            
            # Generate suggested parameters
            suggested_params = self._generate_suggested_params(analysis_results[0])
            
            return (visual_features, style_vectors, suggested_params)
            
        except Exception as e:
            logger.error(f"Error in image feature analysis: {str(e)}")
            raise ValidationError(f"Failed to analyze image features: {str(e)}")

class FeatureCombinerNode(Node):
    """Node for combining text and image features"""
    
    RETURN_TYPES = (DataType.TENSOR, DataType.DICT)
    RETURN_NAMES = ("combined_features", "metadata")
    FUNCTION = "execute"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_features": (DataType.TENSOR, {}),
                "image_features": (DataType.TENSOR, {}),
                "combination_method": (["CONCAT", "WEIGHTED", "CROSS_ATTENTION"], {"default": "CONCAT"})
            },
            "optional": {
                "weights": (DataType.DICT, {"default": {"text": 0.5, "image": 0.5}})
            }
        }

    def _validate_inputs(self,
                        text_features: np.ndarray,
                        image_features: np.ndarray) -> None:
        """Validate input tensors"""
        if not isinstance(text_features, np.ndarray):
            raise ValidationError("Text features must be a numpy array")
        if not isinstance(image_features, np.ndarray):
            raise ValidationError("Image features must be a numpy array")
        if len(text_features) != len(image_features):
            raise ValidationError("Text and image feature counts must match")

    def _concat_features(self,
                        text_features: np.ndarray,
                        image_features: np.ndarray) -> np.ndarray:
        """Concatenate text and image features"""
        return np.concatenate([text_features, image_features], axis=1)

    def _weighted_combine(self,
                         text_features: np.ndarray,
                         image_features: np.ndarray,
                         weights: Dict[str, float]) -> np.ndarray:
        """Combine features using weighted sum"""
        # Normalize features
        text_norm = text_features / np.linalg.norm(text_features, axis=1, keepdims=True)
        image_norm = image_features / np.linalg.norm(image_features, axis=1, keepdims=True)
        
        return weights["text"] * text_norm + weights["image"] * image_norm

    def _cross_attention(self,
                        text_features: np.ndarray,
                        image_features: np.ndarray) -> np.ndarray:
        """Combine features using cross-attention"""
        try:
            import torch
            import torch.nn.functional as F
            
            # Convert to torch tensors
            text_tensor = torch.from_numpy(text_features)
            image_tensor = torch.from_numpy(image_features)
            
            # Compute attention scores
            attention = torch.matmul(text_tensor, image_tensor.transpose(0, 1))
            attention = F.softmax(attention, dim=-1)
            
            # Combine features
            combined = torch.matmul(attention, image_tensor)
            
            return combined.numpy()
        except ImportError:
            raise ValidationError("torch required for cross-attention combination")

    def execute(self,
                text_features: np.ndarray,
                image_features: np.ndarray,
                combination_method: str,
                weights: Optional[Dict[str, float]] = None) -> tuple:
        """Execute node functionality"""
        self._validate_inputs(text_features, image_features)
        
        weights = weights or {"text": 0.5, "image": 0.5}
        
        try:
            if combination_method == "CONCAT":
                combined = self._concat_features(text_features, image_features)
            elif combination_method == "WEIGHTED":
                combined = self._weighted_combine(text_features, image_features, weights)
            elif combination_method == "CROSS_ATTENTION":
                combined = self._cross_attention(text_features, image_features)
            else:
                raise ValidationError(f"Unknown combination method: {combination_method}")
            
            metadata = {
                "text_shape": text_features.shape,
                "image_shape": image_features.shape,
                "combined_shape": combined.shape,
                "method": combination_method,
                "weights": weights if combination_method == "WEIGHTED" else None
            }
            
            return (combined, metadata)
            
        except Exception as e:
            logger.error(f"Error in feature combination: {str(e)}")
            raise ValidationError(f"Failed to combine features: {str(e)}")
