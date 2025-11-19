# TryOnDiffusion Architecture

Detailed explanation of the dual UNet architecture.

## Dual UNet Structure

The model consists of two parallel UNets:

1. **Person UNet**: Generates final output
2. **Garment UNet**: Processes garment features

## Key Components

- Cross-attention mechanisms
- Self-attention with pose conditioning
- FiLM layers for feature modulation
- Attention pooling for pose embeddings

See [TryOnDiffusion README](https://github.com/tryonlabs/opentryon/tree/main/tryondiffusion/README.md) for complete architecture details.

