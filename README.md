# MCQ Generator

A streamlined web application that generates multiple choice questions (MCQs) from PDF documents using natural language processing.

## Features

- **PDF Upload**: Drag and drop or click to upload PDF files (up to 500MB)
- **MCQ Generation**: Automatically generates multiple choice questions from PDF content
- **Interactive Exam**: Take the generated exam with a clean, modern interface
- **Real-time Progress**: Track your progress with a visual progress bar and timer
- **Detailed Results**: View your score, accuracy, and review each question
- **Responsive Design**: Works on desktop and mobile devices

## Setup

1. Install dependencies:
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. Install the spaCy English model:
\`\`\`bash
python scripts/install_spacy_model.py
\`\`\`

3. Run the application:
\`\`\`bash
python app.py
\`\`\`

4. Open your browser and go to `http://localhost:5000`

## How It Works

1. **Upload PDF**: Select a PDF document containing the material you want to study
2. **Set Parameters**: Choose the number of MCQ questions (1-20)
3. **Generate Questions**: The system uses NLP to extract key concepts and create multiple choice questions
4. **Take Exam**: Answer the questions in an interactive exam interface
5. **Review Results**: See your score and review correct/incorrect answers

## Technology Stack

- **Backend**: Flask (Python web framework)
- **NLP**: spaCy for natural language processing
- **PDF Processing**: PyPDF2 for text extraction
- **Frontend**: HTML, CSS, JavaScript (no external frameworks)
- **Styling**: Modern CSS with gradients and animations

## Question Generation Process

The MCQ generator uses advanced NLP techniques to:

1. Extract named entities (people, organizations, dates, etc.)
2. Identify key phrases and concepts
3. Create fill-in-the-blank questions
4. Generate plausible distractors (wrong answers)
5. Assess question difficulty levels

## API Endpoints

- `GET /`: Main application interface
- `POST /generate_questions_from_pdf`: Generate MCQs from uploaded PDF

## Configuration

- Maximum file size: 500MB
- Question range: 1-20 questions
- Supported formats: PDF only
- Required: spaCy English model (`en_core_web_sm`)
