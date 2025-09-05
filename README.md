# 📚 MCQ Generator

**MCQ Generator** is a Flask-based web application that generates interactive multiple-choice questions (MCQs) from PDF documents using natural language processing (spaCy). Users can upload PDFs, automatically generate exam-style questions, take the quiz in a modern interface, and review results with accuracy and performance breakdowns.

---

## ✨ Features

- 📄 **PDF Upload** → Drag & drop or select PDF documents (up to 500MB)
- 🧠 **MCQ Generation** → Creates multiple-choice questions using spaCy NLP
- 📝 **Interactive Exam** → Timer, progress bar, and question navigation
- 📊 **Detailed Results** → Score, accuracy, time taken, and review of answers
- 📱 **Responsive UI** → Works smoothly on desktop & mobile

---

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **NLP**: spaCy (`en_core_web_sm`)
- **PDF Processing**: PyPDF2
- **Frontend**: HTML, CSS, JavaScript (served via Flask)
- **Deployment**: Render (free tier)

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/Falguni35/mcq-generator.git
cd mcq-generator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install the spaCy English model

```bash
python scripts/install_spacy_model.py
```

### 4. Run the application

```bash
python app.py
```

### 5. Access the application

Open your browser and go to `http://localhost:5000`

---

## 📖 How It Works

1. **Upload PDF**: Select a PDF document containing the material you want to study
2. **Set Parameters**: Choose the number of MCQ questions (1-20)
3. **Generate Questions**: The system uses NLP to extract key concepts and create multiple choice questions
4. **Take Exam**: Answer the questions in an interactive exam interface
5. **Review Results**: See your score and review correct/incorrect answers

---

## 🔬 Question Generation Process

The MCQ generator uses advanced NLP techniques to:

1. Extract named entities (people, organizations, dates, etc.)
2. Identify key phrases and concepts
3. Create fill-in-the-blank questions
4. Generate plausible distractors (wrong answers)
5. Assess question difficulty levels

---

## 🔌 API Endpoints

- `GET /`: Main application interface
- `POST /generate_questions_from_pdf`: Generate MCQs from uploaded PDF

---

## ⚙️ Configuration

- **Maximum file size**: 500MB
- **Question range**: 1-20 questions
- **Supported formats**: PDF only
- **Required**: spaCy English model (`en_core_web_sm`)

---

## 📁 Project Structure

```
## 📂 Project Structure

mcq-generator/
├── app.py                 # Main Flask application
├── mcq_generator.py       # Core MCQ generation logic
├── install_spacy_model.py # Script to install spaCy English model
├── requirements.txt       # Python dependencies
├── Procfile               # Deployment start command (for Render/Heroku)
├── README.md              # Project documentation
└── __pycache__/           # Auto-generated cache
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

---

## 🐛 Issues & Support

If you encounter any issues or have questions, please [open an issue](https://github.com/Falguni35/mcq-generator/issues) on GitHub.
