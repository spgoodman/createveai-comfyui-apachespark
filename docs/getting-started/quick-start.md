# Quick Start Tutorial

This tutorial will guide you through creating your first workflow using the CreateveAI Apache Spark nodes for ComfyUI.

## Prerequisites

Ensure you have completed the [installation](installation.md) and [configuration](configuration.md) steps.

## Tutorial: Text-to-Image Generation from Dataset

In this tutorial, we'll create a workflow that:
1. Loads text descriptions from a Spark dataset
2. Extracts semantic features
3. Generates images using the descriptions
4. Saves the results

### Step 1: Generate Sample Dataset

1. Start the Jupyter environment:
   ```bash
   # If using Docker:
   docker-compose up -d
   
   # Access Jupyter at http://localhost:8888
   ```

2. Open `examples/notebooks/01_generate_sample_dataset.ipynb`

3. Run all cells to generate the sample dataset

### Step 2: Create ComfyUI Workflow

1. Open ComfyUI in your browser:
   ```
   http://localhost:8181
   ```

2. Add nodes to your workspace:

   a. **Load Dataset**
   - Right-click → CreateveAI/Apache Spark → LoadDatasetNode
   - Configure:
     ```json
     {
       "path": "/data/sample_dataset.parquet",
       "format": "parquet",
       "connection_type": "LOCAL"
     }
     ```

   b. **Extract Features**
   - Add TextFeatureExtractorNode
   - Connect to LoadDatasetNode's "dataset" output
   - Configure:
     ```json
     {
       "text_column": "description",
       "extraction_type": "SEMANTIC_VECTORS"
     }
     ```

   c. **Setup Image Generation**
   - Add EmptyLatentImage node
   - Add CLIPTextEncode node
   - Connect LoadDatasetNode's "description" to CLIPTextEncode

   d. **Generate Image**
   - Add KSampler node
   - Connect:
     - CLIPTextEncode to "positive"
     - EmptyLatentImage to "latent_image"
   - Configure sampling parameters

   e. **Decode Image**
   - Add VAEDecode node
   - Connect KSampler's output to VAEDecode

### Step 3: Load Example Workflow

Alternatively, load our example workflow:

1. Click "Load" in ComfyUI
2. Select `examples/workflows/text_to_image_workflow.json`

### Step 4: Run the Workflow

1. Click the "Queue Prompt" button
2. Watch the progress in the ComfyUI interface
3. Images will be generated based on dataset descriptions

## Understanding the Workflow

### Dataset Loading
- LoadDatasetNode reads the Parquet file using Spark
- Data is loaded efficiently with Arrow optimization
- Dataset metadata is preserved

### Feature Extraction
- TextFeatureExtractorNode processes text descriptions
- Semantic vectors capture meaning
- Features guide image generation

### Image Generation
- Text descriptions feed into CLIP encoder
- KSampler generates latent images
- VAE decodes final images

## Next Steps

1. **Modify the Workflow**
   - Try different sampling parameters
   - Adjust feature extraction settings
   - Add image analysis nodes

2. **Explore Advanced Features**
   - Use QueryNodes for data filtering
   - Add ImageFeatureAnalyzer
   - Combine text and image features

3. **Learn More**
   - Read [Node Documentation](../nodes/)
   - Try [Advanced Workflows](../examples/)
   - Explore [API Reference](../api/)

## Troubleshooting

### Common Issues

1. **Dataset Not Found**
   - Ensure the dataset path is correct
   - Check Docker volume mounting
   - Verify Spark connection

2. **Memory Issues**
   - Adjust Spark memory configuration
   - Reduce batch sizes
   - Enable caching strategically

3. **Slow Processing**
   - Check Spark UI for bottlenecks
   - Optimize feature extraction
   - Use GPU when available

### Getting Help

- Check [FAQ](../faq.md)
- Join our [Discord](https://discord.gg/createveai)
- Create an [Issue](https://github.com/createveai/createveai-apachespark/issues)

## Tips and Best Practices

1. **Performance**
   - Use appropriate batch sizes
   - Enable caching for repeated operations
   - Monitor Spark UI for optimization

2. **Workflow Design**
   - Keep workflows modular
   - Use meaningful node names
   - Document configuration choices

3. **Data Management**
   - Organize datasets clearly
   - Use appropriate file formats
   - Include metadata for tracking
