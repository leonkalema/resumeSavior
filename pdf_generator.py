from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path
import logging
import re

class EnhancedPDFGenerator:
    """Generates professionally formatted PDF resumes with improved layout."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
    def _setup_styles(self):
    
        # Name style (top of resume)
        if 'Name' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Name',
                parent=self.styles['Heading1'],
                fontSize=24,
                leading=36,
                spaceBefore=0,
                spaceAfter=12,
                textColor=colors.HexColor('#1a1a1a'),
                alignment=TA_CENTER,
            ))
        
        # Contact info style
        if 'ContactInfo' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ContactInfo',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                spaceBefore=0,
                spaceAfter=2,
                textColor=colors.HexColor('#333333'),
                alignment=TA_CENTER,
            ))
        
        # Section headings
        if 'SectionHeading' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeading',
                parent=self.styles['Heading2'],
                fontSize=14,
                leading=18,
                spaceBefore=20,
                spaceAfter=8,
                textColor=colors.HexColor('#2c5282'),  # Dark blue
                keepWithNext=True,
                borderWidth=1,
                borderColor=colors.HexColor('#2c5282'),
                borderPadding=(0, 0, 2, 0),  # Bottom border only
            ))
        
        # Job titles
        if 'JobTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='JobTitle',
                parent=self.styles['Heading3'],
                fontSize=12,
                leading=16,
                spaceBefore=12,
                spaceAfter=2,
                textColor=colors.HexColor('#1a1a1a'),
                keepWithNext=True,
                fontName='Helvetica-Bold',
            ))
        
        # Company and dates
        if 'CompanyDate' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CompanyDate',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                spaceBefore=0,
                spaceAfter=6,
                textColor=colors.HexColor('#666666'),
                keepWithNext=True,
            ))
        
        # Bullet points
        if 'Bullet' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Bullet',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                leftIndent=20,
                spaceBefore=2,
                spaceAfter=2,
                bulletIndent=10,
                textColor=colors.HexColor('#333333'),
            ))
        
        # Skills section
        if 'SkillCategory' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SkillCategory',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=14,
                spaceBefore=6,
                spaceAfter=2,
                textColor=colors.HexColor('#2c5282'),
                fontName='Helvetica-Bold',
            ))

    def _parse_sections(self, content: str) -> dict:
        """Parse resume content into structured sections."""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('**') and line.endswith('**'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.strip('*')
                current_content = []
            else:
                if current_section:
                    current_content.append(line)
                elif not current_section and line:
                    if 'HEADER' not in sections:
                        sections['HEADER'] = []
                    sections['HEADER'].append(line)
        
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
            
        return sections

    def _create_header(self, header_content: list) -> list:
        """Create header elements with improved spacing."""
        elements = []
        if header_content:
            # Name
            elements.append(Paragraph(header_content[0], self.styles['Name']))
            
            # Contact info with subtle separator
            contact_info = ' | '.join(header_content[1:])
            elements.append(Paragraph(contact_info, self.styles['ContactInfo']))
            
            # Separator line
            elements.append(Spacer(1, 20))
            
        return elements

    def _format_bullet_points(self, text: str) -> list:
        """Format bullet points with consistent styling."""
        elements = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                if line.startswith(('•', '-', '*')):
                    bullet_text = line.lstrip('•-* ')
                    elements.append(Paragraph(f'• {bullet_text}', self.styles['Bullet']))
                else:
                    elements.append(Paragraph(line, self.styles['Normal']))
        return elements

    def generate_pdf(self, content: str, output_path: Path) -> None:
        """Generate a professionally formatted PDF resume."""
        try:
            # Setup document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Parse sections
            sections = self._parse_sections(content)
            elements = []
            
            # Create header
            if 'HEADER' in sections:
                elements.extend(self._create_header(sections['HEADER']))
            
            # Process main sections
            for section_name, section_content in sections.items():
                if section_name != 'HEADER':
                    # Add section heading
                    elements.append(Paragraph(section_name, self.styles['SectionHeading']))
                    
                    # Process section content
                    if 'Experience' in section_name or 'Education' in section_name:
                        # Split into entries
                        entries = section_content.split('\n\n')
                        for entry in entries:
                            lines = entry.split('\n')
                            if lines:
                                # Job title/degree
                                elements.append(Paragraph(lines[0], self.styles['JobTitle']))
                                if len(lines) > 1:
                                    # Company/institution and date
                                    elements.append(Paragraph(lines[1], self.styles['CompanyDate']))
                                    # Bullet points
                                    elements.extend(self._format_bullet_points('\n'.join(lines[2:])))
                    elif 'Skills' in section_name:
                        # Format skills section
                        skill_lines = section_content.split('\n')
                        for line in skill_lines:
                            if ':' in line:
                                category, skills = line.split(':', 1)
                                elements.append(Paragraph(category + ':', self.styles['SkillCategory']))
                                elements.append(Paragraph(skills.strip(), self.styles['Normal']))
                            else:
                                elements.append(Paragraph(line, self.styles['Normal']))
                    else:
                        # Default formatting for other sections
                        elements.extend(self._format_bullet_points(section_content))
            
            # Build PDF
            doc.build(elements)
            
        except Exception as e:
            logging.error(f"Error generating PDF: {e}")
            raise

def create_enhanced_pdf_resume(content: str, output_path: Path) -> None:
    """Create an enhanced PDF version of the resume."""
    try:
        pdf_generator = EnhancedPDFGenerator()
        pdf_generator.generate_pdf(content, output_path)
    except Exception as e:
        logging.error(f"Failed to create PDF resume: {e}")
        raise

    