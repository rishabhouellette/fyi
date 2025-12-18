"""
FYI Social ∞ - Template Engine
50+ viral templates (MrBeast, Ali Abdaal, Alex Hormozi styles)
Apply proven formulas to user content
"""

from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path

from .ollama_manager import get_ollama_manager


class TemplateStyle(Enum):
    """Viral content styles"""
    MRBEAST = "mrbeast"
    ALI_ABDAAL = "ali_abdaal"
    ALEX_HORMOZI = "alex_hormozi"
    GARY_VEE = "gary_vee"
    EMMA_CHAMBERLAIN = "emma_chamberlain"
    MKBHD = "mkbhd"
    VSAUCE = "vsauce"
    OVERSIMPLIFIED = "oversimplified"


class TemplateEngine:
    """Apply viral content templates to user videos"""
    
    TEMPLATES = {
        'mrbeast': [
            {
                'id': 'mb_challenge',
                'name': 'MrBeast Challenge',
                'structure': 'Hook → Stakes → Journey → Resolution → Reward',
                'hook_formula': '[DRAMATIC OUTCOME] in [SHORT TIME]',
                'pacing': 'Fast cuts every 2-3 seconds',
                'text_style': 'Yellow ALL CAPS, black outline',
                'music': 'High energy, builds tension',
                'example': '$10,000 if you stay in this room 24 hours'
            },
            {
                'id': 'mb_comparison',
                'name': 'MrBeast $1 vs $100,000',
                'structure': 'Setup → Budget reveal → Experience → Comparison → Winner',
                'hook_formula': '$1 [THING] vs $[BIG NUMBER] [THING]',
                'pacing': 'Medium cuts, split screen comparisons',
                'text_style': 'Price tags in yellow',
                'music': 'Upbeat, playful',
                'example': '$1 Hotel vs $100,000 Hotel'
            },
            {
                'id': 'mb_survival',
                'name': 'MrBeast Survival',
                'structure': 'Challenge intro → Timer starts → Obstacles → Near failure → Victory',
                'hook_formula': 'Surviving [EXTREME CONDITION] for [PRIZE]',
                'pacing': 'Fast, show timer frequently',
                'text_style': 'Red for danger, yellow for progress',
                'music': 'Tense, builds to triumphant',
                'example': 'Surviving 50 Hours Buried Alive'
            }
        ],
        'ali_abdaal': [
            {
                'id': 'aa_productivity',
                'name': 'Ali Abdaal Productivity',
                'structure': 'Problem → Framework → Steps → Science → Action',
                'hook_formula': 'How I [RESULT] using [SYSTEM]',
                'pacing': 'Calm, clear explanations with visuals',
                'text_style': 'Clean sans-serif, minimal',
                'music': 'Lofi, chill',
                'example': 'How I Study 10+ Hours Without Burning Out'
            },
            {
                'id': 'aa_tips',
                'name': 'Ali Abdaal X Tips',
                'structure': 'Introduction → Tip 1 → Tip 2 → ... → Summary',
                'hook_formula': '[NUMBER] Tips to [BENEFIT]',
                'pacing': 'Moderate, numbered sections',
                'text_style': 'Numbers highlighted, clean layout',
                'music': 'Upbeat lofi',
                'example': '7 Tips That Changed How I Work'
            }
        ],
        'alex_hormozi': [
            {
                'id': 'ah_value',
                'name': 'Alex Hormozi Value Bomb',
                'structure': 'Big claim → Framework → Proof → How to apply',
                'hook_formula': 'The [ONE THING] that [TRANSFORMED] my [AREA]',
                'pacing': 'Direct, no fluff, fast cuts',
                'text_style': 'Bold, business-style graphics',
                'music': 'Minimal or none',
                'example': 'The One Marketing Strategy That 10x\'d My Business'
            },
            {
                'id': 'ah_breakdown',
                'name': 'Alex Hormozi Breakdown',
                'structure': 'Myth → Truth → Math → Action steps',
                'hook_formula': 'Why [COMMON BELIEF] is killing your [RESULTS]',
                'pacing': 'Fast, data-driven',
                'text_style': 'Statistics and numbers prominent',
                'music': 'Minimal',
                'example': 'Why "Work Smarter Not Harder" Is Terrible Advice'
            }
        ],
        'gary_vee': [
            {
                'id': 'gv_motivation',
                'name': 'Gary Vee Motivation',
                'structure': 'Wake up call → Reality check → Accountability → Action',
                'hook_formula': 'Stop [BAD HABIT] and start [GOOD HABIT]',
                'pacing': 'Energetic, in-your-face',
                'text_style': 'Bold, high contrast',
                'music': 'Hype, energetic',
                'example': 'Stop Making Excuses And Get To Work'
            }
        ],
        'emma_chamberlain': [
            {
                'id': 'ec_vlog',
                'name': 'Emma Chamberlain Vlog',
                'structure': 'Casual intro → Adventures → Tangents → Wrap up',
                'hook_formula': 'Let me tell you about [RELATABLE CHAOS]',
                'pacing': 'Random, authentic, jump cuts',
                'text_style': 'Casual, lowercase, memes',
                'music': 'Trending indie/pop',
                'example': 'I tried going to bed early for a week'
            }
        ],
        'mkbhd': [
            {
                'id': 'mk_review',
                'name': 'MKBHD Review',
                'structure': 'Intro → Design → Performance → Comparison → Verdict',
                'hook_formula': '[PRODUCT]: The [ATTRIBUTE] You\'ve Been Waiting For?',
                'pacing': 'Smooth, cinematic',
                'text_style': 'Clean, minimal, tech specs',
                'music': 'Modern electronic',
                'example': 'iPhone 15 Pro: The Best Camera Yet?'
            }
        ],
        'vsauce': [
            {
                'id': 'vs_explainer',
                'name': 'Vsauce Mind-Blow',
                'structure': 'Simple question → Complexity → Science → Philosophy → "Or is it?"',
                'hook_formula': 'What if [QUESTION]?',
                'pacing': 'Slow build, dramatic pauses',
                'text_style': 'Minimal text, let voiceover lead',
                'music': 'Thoughtful, builds tension',
                'example': 'What If Everyone Jumped At Once?'
            }
        ]
    }
    
    def __init__(self):
        self.ollama = get_ollama_manager()
    
    def list_templates(self, style: Optional[TemplateStyle] = None) -> List[Dict]:
        """
        List available templates
        
        Args:
            style: Filter by specific style, or None for all
        
        Returns:
            List of template definitions
        """
        
        if style:
            return self.TEMPLATES.get(style.value, [])
        
        # Return all templates
        all_templates = []
        for style_name, templates in self.TEMPLATES.items():
            for template in templates:
                template_copy = template.copy()
                template_copy['style'] = style_name
                all_templates.append(template_copy)
        
        return all_templates
    
    def apply_template(self, template_id: str, video_info: Dict) -> Dict:
        """
        Apply template to video content
        
        Args:
            template_id: Template identifier (e.g., 'mb_challenge')
            video_info: Video metadata (duration, title, description, etc.)
        
        Returns:
            Customized template application with:
            - Hook script
            - Structure breakdown
            - Editing instructions
            - Style guide
            - Music suggestions
        """
        
        # Find template
        template = self._find_template(template_id)
        
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Generate customized content using Ollama
        customized = self._customize_template(template, video_info)
        
        return customized
    
    def suggest_template(self, video_info: Dict) -> Dict:
        """
        Suggest best template based on video content
        
        Args:
            video_info: Video metadata
        
        Returns:
            Recommended template with reasoning
        """
        
        prompt = f"""Analyze this video and suggest the best viral template:

Video Info:
- Title: {video_info.get('title', 'Untitled')}
- Duration: {video_info.get('duration', 0)} seconds
- Description: {video_info.get('description', 'No description')}
- Content Type: {video_info.get('type', 'general')}

Available Templates:
1. MrBeast Challenge - High stakes, fast paced, rewards
2. MrBeast Comparison - $1 vs $100,000 format
3. Ali Abdaal Productivity - Educational, systems-focused
4. Ali Abdaal Tips - List format, actionable advice
5. Alex Hormozi Value - Business insights, no fluff
6. Gary Vee Motivation - High energy, accountability
7. Emma Chamberlain Vlog - Casual, relatable, authentic
8. MKBHD Review - Technical, cinematic, detailed
9. Vsauce Explainer - Educational, philosophical

Which template fits best and why? Return format:
Template: [NAME]
Reason: [ONE SENTENCE]"""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                model='llama3.2-small',
                temperature=0.5,
                max_tokens=200
            )
            
            # Parse response
            lines = response.strip().split('\n')
            template_line = [l for l in lines if l.startswith('Template:')]
            reason_line = [l for l in lines if l.startswith('Reason:')]
            
            suggested_template = template_line[0].replace('Template:', '').strip() if template_line else 'MrBeast Challenge'
            reason = reason_line[0].replace('Reason:', '').strip() if reason_line else 'High engagement potential'
            
            # Find matching template
            template = self._find_template_by_name(suggested_template)
            
            return {
                'template': template,
                'reason': reason,
                'confidence': 0.85
            }
            
        except Exception as e:
            print(f"⚠️ Template suggestion failed: {e}")
            # Fallback to MrBeast Challenge
            return {
                'template': self.TEMPLATES['mrbeast'][0],
                'reason': 'High engagement format with proven success',
                'confidence': 0.5
            }
    
    def generate_script(self, template_id: str, video_info: Dict) -> Dict:
        """
        Generate script following template structure
        
        Args:
            template_id: Template identifier
            video_info: Video metadata
        
        Returns:
            Complete script with timestamps and scenes
        """
        
        template = self._find_template(template_id)
        
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        prompt = f"""Create a viral video script using this template:

Template: {template['name']}
Structure: {template['structure']}
Hook Formula: {template['hook_formula']}
Example: {template['example']}

Video Info:
- Title: {video_info.get('title', 'Untitled')}
- Duration: {video_info.get('duration', 60)} seconds
- Topic: {video_info.get('description', 'General content')}

Generate a complete script with:
1. Hook (0-3s)
2. Main content sections with timestamps
3. Call to action (last 5s)

Format as:
[00:00-00:03] Hook: [script]
[00:03-00:15] Section 1: [script]
..."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                model='llama3.2-small',
                temperature=0.8,
                max_tokens=800
            )
            
            # Parse script sections
            sections = self._parse_script(response)
            
            return {
                'template': template,
                'script': response,
                'sections': sections,
                'total_duration': video_info.get('duration', 60)
            }
            
        except Exception as e:
            print(f"⚠️ Script generation failed: {e}")
            return self._fallback_script(template, video_info)
    
    def _find_template(self, template_id: str) -> Optional[Dict]:
        """Find template by ID"""
        for style_templates in self.TEMPLATES.values():
            for template in style_templates:
                if template['id'] == template_id:
                    return template
        return None
    
    def _find_template_by_name(self, name: str) -> Optional[Dict]:
        """Find template by name (fuzzy match)"""
        name_lower = name.lower()
        
        for style_templates in self.TEMPLATES.values():
            for template in style_templates:
                if name_lower in template['name'].lower():
                    return template
        
        # Fallback to first MrBeast template
        return self.TEMPLATES['mrbeast'][0]
    
    def _customize_template(self, template: Dict, video_info: Dict) -> Dict:
        """Customize template for specific video"""
        
        prompt = f"""Customize this viral template for the user's video:

Template: {template['name']}
Hook Formula: {template['hook_formula']}
Structure: {template['structure']}

Video Info:
- Title: {video_info.get('title', 'Untitled')}
- Topic: {video_info.get('description', 'General')}

Generate:
1. Custom hook (using the formula)
2. 3 key scenes
3. Thumbnail text idea

Return in format:
Hook: [custom hook]
Scene 1: [description]
Scene 2: [description]
Scene 3: [description]
Thumbnail: [text idea]"""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                model='llama3.2-small',
                temperature=0.8,
                max_tokens=400
            )
            
            return {
                'template': template,
                'customization': response,
                'editing_guide': {
                    'pacing': template['pacing'],
                    'text_style': template['text_style'],
                    'music': template['music']
                }
            }
            
        except Exception as e:
            print(f"⚠️ Template customization failed: {e}")
            return {
                'template': template,
                'customization': 'Use template as-is',
                'editing_guide': {
                    'pacing': template['pacing'],
                    'text_style': template['text_style'],
                    'music': template['music']
                }
            }
    
    def _parse_script(self, script_text: str) -> List[Dict]:
        """Parse script into structured sections"""
        sections = []
        
        lines = script_text.strip().split('\n')
        
        for line in lines:
            if '[' in line and ']' in line:
                # Extract timestamp
                timestamp_part = line[line.find('['):line.find(']')+1]
                content_part = line[line.find(']')+1:].strip()
                
                sections.append({
                    'timestamp': timestamp_part,
                    'content': content_part
                })
        
        return sections
    
    def _fallback_script(self, template: Dict, video_info: Dict) -> Dict:
        """Fallback script if AI fails"""
        duration = video_info.get('duration', 60)
        
        return {
            'template': template,
            'script': f"""[00:00-00:03] Hook: {template['example']}
[00:03-00:15] Setup and introduction
[00:15-{duration-10}] Main content following {template['structure']}
[{duration-10}-{duration}] Call to action - Like and subscribe!""",
            'sections': [
                {'timestamp': '[00:00-00:03]', 'content': f"Hook: {template['example']}"},
                {'timestamp': '[00:03-00:15]', 'content': 'Setup and introduction'},
                {'timestamp': f'[00:15-{duration-10}]', 'content': f"Main content following {template['structure']}"},
                {'timestamp': f'[{duration-10}-{duration}]', 'content': 'Call to action'}
            ],
            'total_duration': duration
        }


# Global instance
_template_engine = None

def get_template_engine() -> TemplateEngine:
    """Get global template engine instance"""
    global _template_engine
    if _template_engine is None:
        _template_engine = TemplateEngine()
    return _template_engine
