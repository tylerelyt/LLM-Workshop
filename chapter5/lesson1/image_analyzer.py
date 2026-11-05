from openai import OpenAI
import os
import base64
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
import mimetypes
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vl_text_summary.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VLTextSummarizer:
    """A class for image text recognition and summarization using Qwen-VL-Max."""
    
    SUPPORTED_FORMATS = {
        'PNG': 'image/png',
        'JPEG': 'image/jpeg',
        'JPG': 'image/jpeg',
        'WEBP': 'image/webp'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the VLTextSummarizer with API credentials."""
        load_dotenv()  # Load environment variables from .env file
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("API key must be provided either directly or through DASHSCOPE_API_KEY environment variable")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        logger.info("VLTextSummarizer initialized successfully")

    def encode_image(self, image_path: str) -> str:
        """
        Encode an image file to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string of the image
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {str(e)}")
            raise

    def get_image_format(self, image_path: str) -> str:
        """
        Get the format/mime-type of an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            MIME type string for the image
        """
        try:
            with Image.open(image_path) as img:
                format = img.format
                if format not in self.SUPPORTED_FORMATS:
                    raise ValueError(f"Unsupported image format: {format}. Supported formats: {list(self.SUPPORTED_FORMATS.keys())}")
                return self.SUPPORTED_FORMATS[format]
        except Exception as e:
            logger.error(f"Error determining image format for {image_path}: {str(e)}")
            raise

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """
        Analyze an image using Qwen-VL-Max model.
        
        Args:
            image_path: Path to the image file
            prompt: Question or prompt for the model
            
        Returns:
            Model's response/analysis of the image
        """
        try:
            # Validate image path
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")

            # Encode image and get format
            base64_image = self.encode_image(image_path)
            image_format = self.get_image_format(image_path)
            
            # Create completion request
            completion = self.client.chat.completions.create(
                model="qwen-vl-max-latest",
                messages=[
                    {
                        "role": "system",
                        "content": [{"type": "text", "text": "You are a helpful assistant."}]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_format};base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            response = completion.choices[0].message.content
            logger.info(f"Successfully analyzed image: {image_path}")
            return response

        except Exception as e:
            logger.error(f"Error analyzing image {image_path}: {str(e)}")
            raise

def analyze_document(image_path: str):
    """Example function demonstrating document analysis capabilities."""
    try:
        # Initialize analyzer
        analyzer = VLTextSummarizer()
        
        # Content-focused analysis prompt
        analysis_prompt = """请对这个文档的内容进行深入分析，重点关注以下方面：

一、核心内容提取
1. 文档的主要主题是什么
2. 包含了哪些关键信息和观点
3. 有什么重要的数据或论述
  
二、内容结构分析
1. 主要论述的逻辑框架
2. 各部分内容之间的关联
3. 论述的展开方式
  
三、重点信息识别
1. 最重要的论点或结论
2. 支撑论点的关键证据
3. 特别强调或突出的内容
  
四、内容价值评估
1. 信息的重要性和价值
2. 论述的完整性和深度
3. 内容的创新性或独特见解
  
五、实用性分析
1. 内容的应用价值
2. 对目标受众的帮助
3. 可能的实践指导
  
请进行详细分析，并在最后用2-3句话总结文档的核心价值。"""
        
        print("\n=== 文档内容分析 ===")
        response = analyzer.analyze_image(image_path, analysis_prompt)
        print(response)
            
    except Exception as e:
        print(f"分析过程中出现错误: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    image_path = "sample_image.jpg"  # 替换为你的图片路径
    analyze_document(image_path) 