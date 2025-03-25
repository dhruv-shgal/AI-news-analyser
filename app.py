import streamlit as st
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
import time
import random
import spacy
import math

# Download NLTK data
@st.cache_resource
def download_nltk_data():
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon')

download_nltk_data()

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Load spaCy model
@st.cache_resource
def load_spacy_model():
    return spacy.load("en_core_web_sm")

nlp = load_spacy_model()

def search_company_news(company_name, num_articles=10, page=0):
    """
    Search for company news articles with pagination support
    
    Args:
        company_name: Name of the company
        num_articles: Number of articles to retrieve
        page: Page number for pagination (0-based)
        
    Returns:
        List of article dictionaries with title and URL
    """
    search_query = f"{company_name} company news"
    # Add pagination parameter for Google search
    start_param = f"&start={page * 10}" if page > 0 else ""
    url = f"https://www.google.com/search?q={search_query}&tbm=nws{start_param}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            st.error(f"Failed to fetch page {page}: {response.status_code}. Google might be blocking the request.")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        news_divs = soup.find_all('div', class_='SoaBEf')
        
        for div in news_divs:
            headline_element = div.find('div', class_='mCBkyc')
            headline = headline_element.text if headline_element else "No headline"
            
            skip_titles = ["access denied", "just a moment", "interstitial", "captcha", "403 forbidden"]
            if any(skip_title in headline.lower() for skip_title in skip_titles):
                continue
                
            link_element = div.find('a')
            link = link_element['href'] if link_element else ""
            
            if link.startswith('/url?'):
                link = re.search(r'url=(.*?)&', link)
                link = link.group(1) if link else ""
            
            if link and not any(article['url'] == link for article in articles):
                articles.append({
                    'title': headline,
                    'url': link
                })
        
        return articles
    except Exception as e:
        st.error(f"Error searching for news (page {page}): {str(e)}")
        return []

def extract_article_content(url, retry_count=0):
    """Extract article content with retry mechanism"""
    if retry_count > 2:  # Limit retry attempts
        return {'valid': False}
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.89 Safari/537.36",
            "Referer": "https://www.google.com/"
        }
        
        response = requests.get(url, headers=headers, timeout=15)  # Increased timeout
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.text if soup.title else "Unknown Title"
        
        skip_titles = ["access denied", "just a moment", "interstitial", "captcha", "403 forbidden"]
        if any(skip_title in title.lower() for skip_title in skip_titles):
            # Try with a different user agent on retry
            if retry_count < 2:
                time.sleep(random.uniform(1.5, 3.0))  # Wait longer between retries
                new_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                    "Referer": "https://www.google.com/"
                }
                response = requests.get(url, headers=new_headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.text if soup.title else "Unknown Title"
                if any(skip_title in title.lower() for skip_title in skip_titles):
                    return {'valid': False}
            else:
                return {'valid': False}
        
        article_content = None
        for container in [
            soup.find('article'),
            soup.find('div', class_=['article-content', 'article-body', 'story-content', 'post-content', 'entry-content']),
            soup.find('div', {'id': ['article-content', 'article-body', 'story-content', 'post-content', 'entry-content']}),
            # Add more potential content containers
            soup.find('main'),
            soup.find('div', class_=['content', 'main-content', 'article'])
        ]:
            if container:
                article_content = container
                break
        
        if article_content:
            paragraphs = article_content.find_all('p')
        else:
            paragraphs = [p for p in soup.find_all('p') if len(p.text.strip()) > 20]  # Reduced from 30 to 20
        
        text = ' '.join([p.text.strip() for p in paragraphs])
        
        # Reduced minimum text length from 100 to 80
        if len(text.strip()) < 80:
            # If we have some content but it's less than 80 chars, still consider it valid
            if len(text.strip()) > 30:
                text = f"{title}. {text}"  # Append title to beef up content
            else:
                return {'valid': False}
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        summary = ' '.join(sentences[:7]) if len(sentences) > 7 else text
        
        if len(summary) < 80 and len(text) > 80:
            summary = text[:500] + "..." if len(text) > 500 else text
        
        if len(summary) > 500:
            summary = summary[:497] + "..."
        
        return {
            'valid': True,
            'title': title,
            'text': text,
            'summary': summary
        }
    except Exception as e:
        if retry_count < 2:
            # Wait and retry
            time.sleep(random.uniform(1.5, 3.0))
            return extract_article_content(url, retry_count + 1)
        else:
            return {
                'valid': False,
                'title': "Extraction Failed",
                'text': "",
                'summary': f"Could not extract content from this URL. Error: {str(e)}"
            }

def analyze_company_news(company_name, min_articles=10, max_articles=50):
    """
    Analyze company news with minimum and maximum article constraints
    
    Args:
        company_name: Name of the company
        min_articles: Minimum number of articles to retrieve
        max_articles: Maximum number of articles to retrieve
        
    Returns:
        Analysis results or None if insufficient articles found
    """
    st.info(f"Searching for {min_articles}-{max_articles} articles about {company_name}...")
    
    valid_articles = []
    page = 0
    max_pages = 5  # Limit to 5 pages of Google News results
    
    # Progress bar for article fetching
    progress_bar = st.progress(0)
    
    while len(valid_articles) < max_articles and page < max_pages:
        # Calculate how many more articles we need
        articles_needed = max(min_articles - len(valid_articles), 10)  # At least try to get 10 per page
        
        # Show progress updates
        st.info(f"Searching page {page+1}... (Found {len(valid_articles)} valid articles so far)")
        
        # Fetch articles from current page
        fetched_articles = search_company_news(company_name, articles_needed, page)
        
        if not fetched_articles:
            st.warning(f"No more news articles found on page {page+1}")
            if page > 0:  # Only break if we've already checked at least one page
                break
            else:
                page += 1
                continue
        
        # Process each article
        for idx, article in enumerate(fetched_articles):
            # Update progress
            progress_percentage = min(0.9, (len(valid_articles) / max_articles)) 
            progress_bar.progress(progress_percentage, f"Processing article {idx+1}/{len(fetched_articles)} on page {page+1}")
            
            if len(valid_articles) >= max_articles:
                break
            
            # Add random delay between requests to avoid being blocked
            time.sleep(random.uniform(0.8, 2.0))
            
            try:
                content = extract_article_content(article['url'])
                
                if content.get('valid', False):
                    article.update({
                        'title': content['title'],
                        'text': content['text'],
                        'summary': content['summary'],
                        'topics': extract_topics(content['summary'])
                    })
                    article['sentiment'] = analyze_sentiment(article['text'])
                    valid_articles.append(article)
                    
                    # Show real-time updates
                    if len(valid_articles) % 5 == 0:
                        st.info(f"Found {len(valid_articles)} valid articles...")
            except Exception as e:
                st.warning(f"Failed to process article: {str(e)}")
                continue
        
        # Move to next page if we need more articles
        page += 1
    
    # Complete the progress bar
    progress_bar.progress(1.0, "Article collection complete")
    
    if len(valid_articles) < min_articles:
        st.warning(f"Only found {len(valid_articles)} valid articles, which is less than the minimum {min_articles} requested.")
        if len(valid_articles) == 0:
            return None
    
    return {
        'company_name': company_name,
        'articles': valid_articles,
        'comparison': compare_sentiment(valid_articles)
    }

# Streamlit app
def main():
    st.title("🔍 Company News Sentiment Analyzer")
    
    company_name = st.text_input("Select a company:")
    
    col1, col2 = st.columns(2)
    with col1:
        min_articles = st.number_input("Minimum articles to analyze:", min_value=1, max_value=50, value=10)
    with col2:
        max_articles = st.number_input("Maximum articles to analyze:", min_value=min_articles, max_value=50, value=30)
    
    if st.button("Analyze News"):
        if company_name:
            with st.spinner(f"Searching for news about {company_name}..."):
                results = analyze_company_news(company_name, min_articles, max_articles)
                
                if results:
                    st.success(f"Analysis completed for {company_name}! Found {len(results['articles'])} articles.")
                    
                    tab1, = st.tabs(["Output"])
                    
                    with tab1:
                        st.header("Output")
                        output = format_output(company_name, results['articles'])
                        st.json(output)
                else:
                    st.error(f"No valid news articles found for {company_name} or analysis failed.")
        else:
            st.warning("Please select a company.")

# The rest of the functions remain the same
def analyze_sentiment(text):
    if not text:
        return {'compound': 0, 'pos': 0, 'neg': 0, 'neu': 0, 'label': 'neutral'}
    
    scores = sia.polarity_scores(text)
    compound = scores['compound']
    
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    
    return {
        'compound': compound,
        'pos': scores['pos'],
        'neg': scores['neg'],
        'neu': scores['neu'],
        'label': label
    }

def compare_sentiment(articles):
    if not articles:
        return {
            'sentiment_distribution': {'positive': 0, 'neutral': 0, 'negative': 0}
        }
    
    sentiment_labels = [article['sentiment']['label'] for article in articles]
    sentiment_distribution = {
        'positive': sentiment_labels.count('positive'),
        'neutral': sentiment_labels.count('neutral'),
        'negative': sentiment_labels.count('negative')
    }
    
    return {
        'sentiment_distribution': sentiment_distribution
    }

def extract_topics(summary):
    """Extract topics from summary using spaCy NER and keyword matching"""
    if not summary:
        return ["General News"]
    
    doc = nlp(summary)
    entities = {ent.text.lower() for ent in doc.ents if ent.label_ in ["ORG", "PRODUCT", "EVENT", "LAW", "GPE"]}
    
    topic_categories = {
        "Electric Vehicles": ["electric vehicle", "ev", "battery", "tesla model"],
        "Stock Market": ["stock", "market", "shares", "invest", "trading"],
        "Innovation": ["innovation", "technology", "new product", "research"],
        "Regulations": ["regulation", "regulatory", "law", "policy", "compliance"],
        "Autonomous Vehicles": ["autonomous", "self-driving", "driverless", "autopilot"],
        "Financial": ["financial", "revenue", "profit", "sales", "earnings"],
        "Partnerships": ["partnership", "collaboration", "deal", "agreement"],
        "Legal": ["lawsuit", "legal", "court", "dispute"]
    }
    
    topics = set()
    summary_lower = summary.lower()
    
    for topic, keywords in topic_categories.items():
        if any(keyword in summary_lower for keyword in keywords) or \
           any(entity in summary_lower for entity in entities if any(keyword in entity for keyword in keywords)):
            topics.add(topic)
    
    return list(topics) if topics else ["General News"]

def analyze_coverage_differences(articles):
    """Analyze coverage differences across all articles"""
    if len(articles) < 2:
        return []
    
    differences = []
    for i in range(len(articles)):
        for j in range(i + 1, len(articles)):
            art1, art2 = articles[i], articles[j]
            sentiment1, sentiment2 = art1['sentiment']['label'], art2['sentiment']['label']
            topics1, topics2 = art1['topics'], art2['topics']
            
            comparison = f"Article {i+1} ({art1['title'][:30]}...) has {sentiment1} sentiment focusing on {', '.join(topics1[:2])}, " \
                        f"while Article {j+1} ({art2['title'][:30]}...) has {sentiment2} sentiment focusing on {', '.join(topics2[:2])}."
            impact = f"Article {i+1} may {'boost confidence' if sentiment1 == 'positive' else 'raise concerns'}, " \
                    f"while Article {j+1} may {'boost confidence' if sentiment2 == 'positive' else 'raise concerns'}."
            
            differences.append({"Comparison": comparison, "Impact": impact})
    
    return differences

def analyze_topic_overlap(articles):
    """Analyze topic overlap and unique topics across all articles"""
    if not articles:
        return {"Common Topics": [], "Unique Topics": {}}
    
    # Get all topics for each article
    all_topics = [set(article['topics']) for article in articles]
    
    # Common topics: intersection of all articles' topics
    common_topics = set.intersection(*all_topics) if all_topics else set()
    
    # Unique topics: topics that appear in only one article
    unique_topics = {}
    topic_counts = {}
    
    # Count occurrences of each topic across all articles
    for i, topics in enumerate(all_topics, 1):
        for topic in topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Assign unique topics to each article
    for i, topics in enumerate(all_topics, 1):
        unique = [topic for topic in topics if topic_counts[topic] == 1]
        unique_topics[f"Article {i}"] = unique if unique else list(topics)  # If no unique, use all topics
    
    return {
        "Common Topics": list(common_topics),
        "Unique Topics": unique_topics
    }

def generate_final_sentiment(articles, company_name):
    """Generate final sentiment analysis based on all summaries"""
    if not articles:
        return f"No sufficient data to analyze {company_name}'s news coverage."
    
    sentiment_dist = compare_sentiment(articles)['sentiment_distribution']
    total = sum(sentiment_dist.values())
    if total == 0:
        return f"{company_name}'s news coverage analysis inconclusive due to lack of data."
    
    positive_pct = sentiment_dist['positive'] / total
    negative_pct = sentiment_dist['negative'] / total
    neutral_pct = sentiment_dist['neutral'] / total
    
    summaries = [article['summary'] for article in articles]
    combined_summary = " ".join(summaries)
    overall_sentiment = analyze_sentiment(combined_summary)
    compound_score = overall_sentiment['compound']
    
    analysis = f"{company_name}'s news coverage shows {sentiment_dist['positive']} positive, " \
              f"{sentiment_dist['negative']} negative, and {sentiment_dist['neutral']} neutral articles. "
    
    if positive_pct > 0.6 and compound_score > 0.2:
        analysis += "The overall sentiment is strongly positive, suggesting good performance and potential growth."
    elif negative_pct > 0.6 and compound_score < -0.2:
        analysis += "The overall sentiment is strongly negative, indicating significant challenges ahead."
    elif positive_pct > negative_pct and compound_score > 0:
        analysis += "The sentiment leans positive, indicating a generally favorable outlook with some stability."
    elif negative_pct > positive_pct and compound_score < 0:
        analysis += "The sentiment leans negative, suggesting caution due to prevailing challenges."
    else:
        analysis += "The sentiment is balanced, reflecting a mixed outlook with no clear trend."
    
    return analysis

def format_output(company_name, articles):
    """Format the output with all required fields"""
    formatted_articles = []
    for article in articles:
        formatted_articles.append({
            "TITLE": article['title'],
            "SUMMARY": article['summary'],
            "SENTIMENT": article['sentiment']['label'].capitalize(),
            "TOPICS": article['topics']
        })
    
    sentiment_distribution = compare_sentiment(articles)['sentiment_distribution']
    
    return {
        "COMPANY": company_name,
        "ARTICLES": formatted_articles,
        "COMPARATIVE_SENTIMENT_SCORE": {
            "SENTIMENT_DISTRIBUTION": {
                "POSITIVE": sentiment_distribution['positive'],
                "NEGATIVE": sentiment_distribution['negative'],
                "NEUTRAL": sentiment_distribution['neutral']
            }
        },
        "Coverage Differences": analyze_coverage_differences(articles),
        "Topic Overlap": analyze_topic_overlap(articles),
        "Final Sentiment Analysis": generate_final_sentiment(articles, company_name),
        "Audio": "[Play Hindi Speech]"
    }

if __name__ == "_main_":
    main()