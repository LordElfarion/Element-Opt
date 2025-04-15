<h1>🌐✨ Element Opt – AI-Powered Basic SEO & Content Idea Generator</h1>
Element Opt is a lightweight, beginner-friendly tool that uses AI to help improve your website's SEO and generate fresh content ideas for social media and video platforms. Perfect for creators, startups, and anyone looking to optimize without the complexity.
<br><br>
🔍 Website SEO Checker
Scan any website and get basic, actionable suggestions to improve search visibility—no technical skills needed.
<br><br>
💡 Social Media Content Ideas
Generate AI-powered ideas for posts across major platforms to keep your content fresh and engaging.
<br><br>
🎥 Basic Video SEO Assistant
<br>
<br>
Plan better video content with:
<br><br>
✏️ Optimized titles
<br><br>
🖼️ Thumbnail ideas
<br><br>
🎯 Hooks & outlines
<br><br>
🔑 Relevant keywords
<br><br>
<br>
⚠️ Note: Element Opt is currently in its early stages – it's a basic tool with essential features. More powerful options are on the way!
<br><br>
<br>
🚀 Start optimizing smarter with Element Opt – simple, helpful, and powered by AI.
<br><br>
<br><br>
<br><br>
<h1>⚙️ Backend Setup – Element Opt</h1>
This is the backend of Element Opt – a simple AI-powered tool that offers website SEO suggestions, content ideas for social media, and basic video optimization tips.

🧰 Built With

🧠 Python

🤖 OpenAI API (for content & SEO idea generation)

🚀 Getting Started
1. Clone the Repository

git clone https://github.com/Tlgru/Element-Opt.git
cd Element-Opt/backend

3. Create a Virtual Environment

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

3. Install Dependencies

pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file in the backend/ directory and add the following variables:

OPENAI_API_KEY=your_openai_api_key
MONGO_URI=your_mongodb_connection_string

Replace your_openai_api_key and your_mongodb_connection_string with your actual OpenAI API key and MongoDB connection string, respectively.

▶️ Run the Server

uvicorn main:app --reload

The API will be available at:

http://localhost:8000

