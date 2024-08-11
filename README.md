# Video background replacement with green screen.

This project improves video background replacement by:

- **Reducing Memory Usage**: Processes videos in chunks instead of storing all frames in memory.
- **Increasing Efficiency**: Uses multiple CPU cores to speed up processing.

This is an enhancement over the method used in the [Hugging Face Background-Remove space](https://huggingface.co/spaces/Pranay009/Background-Remove), which loads the entire video into memory.

## Usage

Simply run the script with your input video, background image, and output paths.

```python
apply_background(input_path, output_path, background_path)
```

# Installation
```bash
pip install -r requirements.txt
```