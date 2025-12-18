"""
FYI Social ∞ - AI Growth Mentor
Analyzes top 500 posts → Weekly AI report
Gives personalized growth advice using Ollama
"""

import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

from .ollama_manager import get_ollama_manager


class GrowthMentor:
    """AI-powered growth mentor analyzing content performance"""
    
    def __init__(self):
        self.ollama = get_ollama_manager()
        self.reports_dir = Path('data/growth_reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_content(self, posts: List[Dict], days: int = 7) -> Dict:
        """
        Analyze user's content performance
        
        Args:
            posts: List of post data with metrics
            days: Number of days to analyze (default 7)
        
        Returns:
            Growth report with insights and recommendations
        """
        
        # Filter posts from last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_posts = [
            post for post in posts
            if datetime.fromisoformat(post.get('posted_at', '2024-01-01'))
            >= cutoff_date
        ]
        
        # Analyze metrics
        metrics = self._calculate_metrics(recent_posts)
        
        # Find patterns
        patterns = self._identify_patterns(recent_posts)
        
        # Generate insights using Ollama
        insights = self._generate_insights(metrics, patterns)
        
        # Create recommendations
        recommendations = self._create_recommendations(metrics, patterns, insights)
        
        # Generate weekly report
        report = {
            'period': f'Last {days} days',
            'generated_at': datetime.now().isoformat(),
            'total_posts': len(recent_posts),
            'metrics': metrics,
            'patterns': patterns,
            'insights': insights,
            'recommendations': recommendations,
            'score': self._calculate_growth_score(metrics)
        }
        
        # Save report
        self._save_report(report)
        
        return report
    
    def analyze_top_performers(self, posts: List[Dict], limit: int = 500) -> Dict:
        """
        Analyze top-performing content across platforms
        
        Args:
            posts: List of all posts
            limit: Number of top posts to analyze (default 500)
        
        Returns:
            Analysis of what makes content perform well
        """
        
        # Sort by engagement
        sorted_posts = sorted(
            posts,
            key=lambda x: self._calculate_engagement_score(x),
            reverse=True
        )
        
        top_posts = sorted_posts[:limit]
        
        # Analyze common traits
        traits = self._analyze_common_traits(top_posts)
        
        # Generate AI analysis
        ai_analysis = self._generate_ai_analysis(top_posts, traits)
        
        return {
            'top_posts_count': len(top_posts),
            'common_traits': traits,
            'ai_analysis': ai_analysis,
            'action_items': self._create_action_items(traits, ai_analysis)
        }
    
    def _calculate_metrics(self, posts: List[Dict]) -> Dict:
        """Calculate performance metrics"""
        
        if not posts:
            return self._empty_metrics()
        
        total_views = sum(post.get('views', 0) for post in posts)
        total_likes = sum(post.get('likes', 0) for post in posts)
        total_comments = sum(post.get('comments', 0) for post in posts)
        total_shares = sum(post.get('shares', 0) for post in posts)
        
        avg_views = total_views / len(posts)
        avg_engagement = (total_likes + total_comments + total_shares) / len(posts)
        
        # Engagement rate
        engagement_rate = (total_likes + total_comments) / total_views * 100 if total_views > 0 else 0
        
        # Best performing post
        best_post = max(posts, key=lambda x: self._calculate_engagement_score(x))
        
        return {
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'total_shares': total_shares,
            'avg_views': round(avg_views, 2),
            'avg_engagement': round(avg_engagement, 2),
            'engagement_rate': round(engagement_rate, 2),
            'best_post_id': best_post.get('id', 'unknown'),
            'best_post_views': best_post.get('views', 0)
        }
    
    def _calculate_engagement_score(self, post: Dict) -> float:
        """Calculate engagement score for a post"""
        views = post.get('views', 0)
        likes = post.get('likes', 0)
        comments = post.get('comments', 0)
        shares = post.get('shares', 0)
        
        # Weighted score
        score = (
            views * 1 +
            likes * 10 +
            comments * 20 +
            shares * 30
        )
        
        return score
    
    def _identify_patterns(self, posts: List[Dict]) -> Dict:
        """Identify patterns in content performance"""
        
        if not posts:
            return {}
        
        # Analyze by platform
        by_platform = defaultdict(list)
        for post in posts:
            platform = post.get('platform', 'unknown')
            by_platform[platform].append(post)
        
        # Analyze by content type
        by_type = defaultdict(list)
        for post in posts:
            content_type = post.get('type', 'unknown')
            by_type[content_type].append(post)
        
        # Analyze by time of day
        by_hour = defaultdict(list)
        for post in posts:
            posted_at = datetime.fromisoformat(post.get('posted_at', '2024-01-01T12:00:00'))
            hour = posted_at.hour
            by_hour[hour].append(post)
        
        # Find best performers
        best_platform = max(
            by_platform.items(),
            key=lambda x: sum(self._calculate_engagement_score(p) for p in x[1])
        )[0] if by_platform else 'unknown'
        
        best_type = max(
            by_type.items(),
            key=lambda x: sum(self._calculate_engagement_score(p) for p in x[1])
        )[0] if by_type else 'unknown'
        
        best_hour = max(
            by_hour.items(),
            key=lambda x: sum(self._calculate_engagement_score(p) for p in x[1])
        )[0] if by_hour else 12
        
        return {
            'best_platform': best_platform,
            'best_content_type': best_type,
            'best_posting_hour': best_hour,
            'platform_distribution': {k: len(v) for k, v in by_platform.items()},
            'type_distribution': {k: len(v) for k, v in by_type.items()}
        }
    
    def _generate_insights(self, metrics: Dict, patterns: Dict) -> List[str]:
        """Generate AI insights using Ollama"""
        
        prompt = f"""As an expert social media growth advisor, analyze this performance data and provide 5 key insights:

METRICS:
- Total Views: {metrics.get('total_views', 0):,}
- Avg Views per Post: {metrics.get('avg_views', 0):,.0f}
- Engagement Rate: {metrics.get('engagement_rate', 0)}%
- Total Posts: {metrics.get('total_likes', 0) + metrics.get('total_comments', 0) + metrics.get('total_shares', 0)}

PATTERNS:
- Best Platform: {patterns.get('best_platform', 'unknown')}
- Best Content Type: {patterns.get('best_content_type', 'unknown')}
- Best Posting Hour: {patterns.get('best_posting_hour', 12)}:00

Provide 5 concise insights (one sentence each) about what's working and what needs improvement.
Be specific and actionable. Return only the insights, numbered 1-5."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                model='llama3.2-small',
                temperature=0.7,
                max_tokens=400
            )
            
            # Parse insights
            lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
            insights = [line.lstrip('0123456789.- ') for line in lines if line]
            
            return insights[:5]
            
        except Exception as e:
            print(f"⚠️ AI insight generation failed: {e}")
            return self._fallback_insights(metrics, patterns)
    
    def _fallback_insights(self, metrics: Dict, patterns: Dict) -> List[str]:
        """Fallback insights if AI fails"""
        return [
            f"Your best platform is {patterns.get('best_platform', 'unknown')} - focus more content here",
            f"Engagement rate of {metrics.get('engagement_rate', 0):.1f}% indicates room for improvement",
            f"Posting at {patterns.get('best_posting_hour', 12)}:00 shows better performance",
            f"Average {metrics.get('avg_views', 0):.0f} views per post - aim for 2x growth",
            "Consistency is key - maintain regular posting schedule"
        ]
    
    def _create_recommendations(self, metrics: Dict, patterns: Dict, insights: List[str]) -> List[Dict]:
        """Create actionable recommendations"""
        
        recommendations = []
        
        # Content frequency recommendation
        if metrics.get('total_views', 0) < 10000:
            recommendations.append({
                'category': 'Posting Frequency',
                'priority': 'High',
                'action': 'Increase posting frequency to 2-3x per day',
                'reason': 'Low total views indicate need for more content volume'
            })
        
        # Engagement recommendation
        if metrics.get('engagement_rate', 0) < 3:
            recommendations.append({
                'category': 'Engagement',
                'priority': 'High',
                'action': 'Add stronger CTAs and questions to boost engagement',
                'reason': f"Current {metrics.get('engagement_rate', 0):.1f}% is below 3% benchmark"
            })
        
        # Platform focus
        best_platform = patterns.get('best_platform', 'unknown')
        if best_platform != 'unknown':
            recommendations.append({
                'category': 'Platform Strategy',
                'priority': 'Medium',
                'action': f'Double down on {best_platform} content',
                'reason': f'{best_platform} shows best performance for your content'
            })
        
        # Timing optimization
        best_hour = patterns.get('best_posting_hour', 12)
        recommendations.append({
            'category': 'Posting Time',
            'priority': 'Medium',
            'action': f'Schedule posts around {best_hour}:00',
            'reason': 'Historical data shows peak engagement at this time'
        })
        
        # Content type focus
        best_type = patterns.get('best_content_type', 'unknown')
        if best_type != 'unknown':
            recommendations.append({
                'category': 'Content Type',
                'priority': 'Low',
                'action': f'Create more {best_type} content',
                'reason': f'{best_type} format performs best for your audience'
            })
        
        return recommendations
    
    def _analyze_common_traits(self, posts: List[Dict]) -> Dict:
        """Analyze common traits in top-performing posts"""
        
        # Analyze duration (for videos)
        durations = [post.get('duration', 0) for post in posts if post.get('duration', 0) > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Analyze caption length
        caption_lengths = [len(post.get('caption', '')) for post in posts]
        avg_caption_length = sum(caption_lengths) / len(caption_lengths) if caption_lengths else 0
        
        # Analyze hashtag usage
        hashtag_counts = [post.get('caption', '').count('#') for post in posts]
        avg_hashtags = sum(hashtag_counts) / len(hashtag_counts) if hashtag_counts else 0
        
        return {
            'avg_duration_seconds': round(avg_duration, 1),
            'avg_caption_length': round(avg_caption_length, 0),
            'avg_hashtags': round(avg_hashtags, 1),
            'most_common_platform': self._most_common([p.get('platform', 'unknown') for p in posts]),
            'most_common_type': self._most_common([p.get('type', 'unknown') for p in posts])
        }
    
    def _most_common(self, items: List) -> str:
        """Find most common item in list"""
        if not items:
            return 'unknown'
        return max(set(items), key=items.count)
    
    def _generate_ai_analysis(self, posts: List[Dict], traits: Dict) -> str:
        """Generate AI analysis of top performers"""
        
        prompt = f"""Analyze these traits from {len(posts)} top-performing social media posts:

TRAITS:
- Average Duration: {traits.get('avg_duration_seconds', 0)} seconds
- Average Caption Length: {traits.get('avg_caption_length', 0)} characters
- Average Hashtags: {traits.get('avg_hashtags', 0)}
- Most Common Platform: {traits.get('most_common_platform', 'unknown')}
- Most Common Type: {traits.get('most_common_type', 'unknown')}

Provide a 3-paragraph analysis of what makes these posts successful and how to replicate this success.
Be specific and actionable."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                model='llama3.2-small',
                temperature=0.7,
                max_tokens=500
            )
            
            return response.strip()
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            return "Unable to generate AI analysis. Please check Ollama connection."
    
    def _create_action_items(self, traits: Dict, ai_analysis: str) -> List[str]:
        """Create action items from analysis"""
        
        items = []
        
        # Duration recommendation
        avg_duration = traits.get('avg_duration_seconds', 0)
        if avg_duration > 0:
            items.append(f"Target {avg_duration:.0f} seconds for video content")
        
        # Caption recommendation
        avg_caption = traits.get('avg_caption_length', 0)
        if avg_caption > 0:
            items.append(f"Write captions around {avg_caption:.0f} characters")
        
        # Hashtag recommendation
        avg_hashtags = traits.get('avg_hashtags', 0)
        items.append(f"Use {avg_hashtags:.0f} hashtags per post")
        
        # Platform focus
        platform = traits.get('most_common_platform', 'unknown')
        if platform != 'unknown':
            items.append(f"Focus content strategy on {platform}")
        
        return items
    
    def _calculate_growth_score(self, metrics: Dict) -> int:
        """Calculate overall growth score (1-100)"""
        
        # Scoring factors
        views_score = min(metrics.get('avg_views', 0) / 1000 * 30, 30)  # Max 30 points
        engagement_score = min(metrics.get('engagement_rate', 0) * 5, 30)  # Max 30 points
        volume_score = min(len(metrics) * 2, 20)  # Max 20 points (10+ posts)
        consistency_score = 20  # Placeholder - would check posting consistency
        
        total = views_score + engagement_score + volume_score + consistency_score
        
        return int(min(total, 100))
    
    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            'total_views': 0,
            'total_likes': 0,
            'total_comments': 0,
            'total_shares': 0,
            'avg_views': 0,
            'avg_engagement': 0,
            'engagement_rate': 0,
            'best_post_id': 'none',
            'best_post_views': 0
        }
    
    def _save_report(self, report: Dict):
        """Save report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'growth_report_{timestamp}.json'
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Growth report saved: {filepath}")


# Global instance
_growth_mentor = None

def get_growth_mentor() -> GrowthMentor:
    """Get global growth mentor instance"""
    global _growth_mentor
    if _growth_mentor is None:
        _growth_mentor = GrowthMentor()
    return _growth_mentor
