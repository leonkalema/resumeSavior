import os
import sys
import logging
import random
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re
from datetime import datetime
import uuid
import json
from pdf_generator import create_enhanced_pdf_resume  

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('resume_customizer.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    """Configuration settings for the resume customizer."""
    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 1500
    temperature: float = 0.82
    resume_dir: Path = Path('repo')
    input_file: str = 'resume.txt'
    style_variations_file: str = 'style_variations.json'

class StyleManager:
    """Manages writing style variations to ensure natural, human-like content."""
    
    DEFAULT_VARIATIONS = {
        "action_verbs": [
            "led", "managed", "developed", "created", "implemented",
            "coordinated", "established", "designed", "launched", "achieved",
            "drove", "spearheaded", "orchestrated", "pioneered", "executed"
        ],
        "transitions": [
            "additionally", "moreover", "furthermore", "also",
            "in addition to", "beyond that", "similarly", "likewise",
            "along with", "equally important"
        ],
        "quantifiers": [
            "approximately", "roughly", "about", "nearly",
            "more than", "up to", "around", "over", "close to"
        ],
    }
    
    def __init__(self, config: Config):
        self.style_file = Path(config.style_variations_file)
        self.variations = self._initialize_variations()
        
    def _initialize_variations(self) -> Dict[str, List[str]]:
        """Initialize or load style variations, creating file if needed."""
        try:
            if not self.style_file.exists():
                # Create directory if it doesn't exist
                self.style_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write default variations to file
                with open(self.style_file, 'w', encoding='utf-8') as f:
                    json.dump(self.DEFAULT_VARIATIONS, f, indent=2)
                logger.info(f"Created new style variations file: {self.style_file}")
                return self.DEFAULT_VARIATIONS
            
            # Load existing variations
            with open(self.style_file, 'r', encoding='utf-8') as f:
                variations = json.load(f)
            logger.info(f"Loaded existing style variations from: {self.style_file}")
            return variations
            
        except Exception as e:
            logger.warning(f"Error loading style variations: {e}. Using defaults.")
            return self.DEFAULT_VARIATIONS

    def get_random_variations(self) -> Dict[str, List[str]]:
        """Get a random subset of style variations."""
        return {
            category: random.sample(words, min(len(words), random.randint(3, 5)))
            for category, words in self.variations.items()
        }

class ResumeCustomizer:
    def __init__(self, config: Config):
        self.config = config
        self._validate_environment()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.style_manager = StyleManager(config)
        
    def _validate_environment(self) -> None:
        """Validate environment setup and required files."""
        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables")
        
        if not self.config.resume_dir.exists():
            raise FileNotFoundError(f"Directory {self.config.resume_dir} not found")

    def generate_filename(self, job_title: str) -> str:
    
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', job_title.lower())
        words = clean_title.split()[:3]
        base_name = '_'.join(words)
        date_str = datetime.now().strftime('%b%d')
        return f"{base_name}_{date_str}_v1"

    async def load_resume(self, resume_path: Path) -> str:
        """Load resume content from file."""
        try:
            with ThreadPoolExecutor() as executor:
                resume_content = await asyncio.get_event_loop().run_in_executor(
                    executor,
                    lambda: resume_path.read_text(encoding='utf-8')
                )
            return resume_content
        except Exception as e:
            logger.error(f"Error loading resume: {e}")
            raise

    async def analyze_job_requirements(self, job_description: str) -> List[str]:
        """Extract key requirements and skills from job description."""
        try:
            messages = [
                {"role": "system", "content": "Extract key requirements and skills from the job description. Return only the list, no explanations."},
                {"role": "user", "content": job_description}
            ]
            
            response = await self.async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip().split('\n')
        except Exception as e:
            logger.error(f"Error analyzing job requirements: {e}")
            return []

    def get_job_details(self) -> Tuple[str, str]:
        """Get job details from user input."""
        print("\nJob title:", end=" ")
        job_title = input().strip()
        
        print("\nPaste job description (press Ctrl+D or type 'END' on a new line when finished):")
        lines = []
        try:
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
        except (KeyboardInterrupt, EOFError):
            if not lines:
                logger.info("Input cancelled")
                sys.exit(0)
        
        return job_title, '\n'.join(lines).strip()

    async def generate_customized_resume(self, resume_content: str, job_title: str, job_description: str) -> str:
        """Generate naturally customized resume with varied writing styles."""
        try:
            style_variations = self.style_manager.get_random_variations()
            key_requirements = await self.analyze_job_requirements(job_description)
            
            prompt_elements = [
                "Adapt this person's resume for the job, maintaining their original voice and experience:",
                f"Job Title: {job_title}",
                "Guidelines:",
                "- Keep the original writing style and tone",
                "- Maintain authentic experiences and achievements",
                "- Use natural language variations",
                "- Include relevant keywords naturally",
                "- Avoid obvious keyword stuffing",
                f"Key skills to emphasize: {', '.join(key_requirements)}",
                f"Suggested action verbs: {', '.join(style_variations['action_verbs'])}",
                "Resume content:",
                resume_content,
                "Job Description:",
                job_description
            ]

            messages = [
                {"role": "system", "content": (
                    "You are the resume owner. Customize your resume while maintaining "
                    "your authentic voice and experience. Use natural language and avoid "
                    "any AI-like patterns or repetitive structures."
                )},
                {"role": "user", "content": "\n\n".join(prompt_elements)}
            ]

            response = await self.async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                presence_penalty=0.4,
                frequency_penalty=0.4
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating customized resume: {e}")
            raise

    async def save_resume(self, content: str, output_path: Path) -> None:
  
        try:
            # Create output directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create separate paths for TXT and PDF
            txt_path = output_path.with_suffix('.txt')
            pdf_path = output_path.with_suffix('.pdf')
            
            # Save TXT version
            with ThreadPoolExecutor() as executor:
                await asyncio.get_event_loop().run_in_executor(
                    executor,
                    lambda: txt_path.write_text(content, encoding='utf-8')
                )
            
            # Generate PDF version
            with ThreadPoolExecutor() as executor:
                await asyncio.get_event_loop().run_in_executor(
                    executor,
                    create_enhanced_pdf_resume,
                    content,
                    pdf_path
                )
                
                logger.info(f"Text version saved to: {txt_path}")
                logger.info(f"PDF version saved to: {pdf_path}")
                
        except Exception as e:
            logger.error(f"Error saving resume: {e}")
            raise


async def main():
    try:
        config = Config()
        customizer = ResumeCustomizer(config)
        
        resume_path = config.resume_dir / config.input_file
        logger.info("Loading resume...")
        resume_content = await customizer.load_resume(resume_path)

        job_title, job_description = customizer.get_job_details()
        logger.info("Analyzing job requirements and generating customized resume...")

        output_filename = customizer.generate_filename(job_title)
        output_path = config.resume_dir / 'outputs' / output_filename

        customized_resume = await customizer.generate_customized_resume(
            resume_content,
            job_title,
            job_description
        )

        await customizer.save_resume(customized_resume, output_path)
        logger.info(f"Resume saved to {output_path}")
        
        print(f"\nResume customized and saved to: {output_path}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())