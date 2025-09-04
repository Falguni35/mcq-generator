from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from mcq_generator import generate_mcqs, is_spacy_available
import logging
import os
from werkzeug.exceptions import BadRequest
import PyPDF2
from datetime import datetime
import uuid
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configuration - 500MB max file size
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large',
        'message': 'File size exceeds 500MB limit'
    }), 413

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(e)
    }), 400

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An error occurred while processing your request'
    }), 500

@app.route('/', methods=['GET'])
def home():
    """MCQ Generator with integrated exam interface"""
    html_template = r'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCQ Generator - Interactive Exam System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                background: white; 
                border-radius: 15px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 40px;
                max-width: 1000px;
                width: 100%;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 { 
                color: #2d3748;
                font-size: 2.5rem; 
                margin-bottom: 10px;
            }
            .header p { 
                color: #718096;
                font-size: 1.1rem;
            }
            .upload-section {
                margin-bottom: 30px;
            }
            .upload-area {
                border: 3px dashed #cbd5e0;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin-bottom: 20px;
                transition: all 0.3s;
                cursor: pointer;
            }
            .upload-area:hover {
                border-color: #667eea;
                background: #f7fafc;
            }
            .upload-area.dragover {
                border-color: #667eea;
                background: #ebf8ff;
            }
            .upload-icon {
                font-size: 3rem;
                color: #a0aec0;
                margin-bottom: 15px;
            }
            .upload-text {
                color: #4a5568;
                font-size: 1.1rem;
                margin-bottom: 10px;
            }
            .upload-subtext {
                color: #718096;
                font-size: 0.9rem;
            }
            #fileInput {
                display: none;
            }
            .file-info {
                display: none;
                background: #f7fafc;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .file-info h4 {
                color: #2d3748;
                margin-bottom: 5px;
            }
            .file-info p {
                color: #718096;
                margin: 2px 0;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #2d3748;
                font-weight: 600;
            }
            .form-group input[type="number"] {
                width: 120px;
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                font-size: 16px;
            }
            .btn {
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                text-decoration: none;
                display: inline-block;
                text-align: center;
            }
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            .btn-primary:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .btn-success {
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
            }
            .btn-success:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(72, 187, 120, 0.3);
            }
            .btn-secondary {
                background: #e2e8f0;
                color: #4a5568;
            }
            .btn-secondary:hover {
                background: #cbd5e0;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 40px;
            }
            .loading-spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .error {
                display: none;
                background: #fed7d7;
                color: #c53030;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #e53e3e;
            }
            .exam-section {
                display: none;
            }
            .exam-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding: 20px;
                background: #f7fafc;
                border-radius: 10px;
            }
            .exam-header h2 {
                color: #2d3748;
                margin: 0;
            }
            .exam-info {
                display: flex;
                gap: 20px;
                font-size: 14px;
                color: #718096;
            }
            .exam-timer {
                font-weight: 600;
                color: #667eea;
            }
            .exam-progress {
                background: #e2e8f0;
                height: 8px;
                border-radius: 4px;
                margin-bottom: 30px;
                overflow: hidden;
            }
            .exam-progress-bar {
                background: linear-gradient(90deg, #667eea, #764ba2);
                height: 100%;
                width: 0%;
                transition: width 0.3s ease;
            }
            .question-container {
                background: white;
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 20px;
                transition: all 0.3s;
            }
            .question-container:hover {
                border-color: #cbd5e0;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .question-number {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 14px;
                color: #718096;
                margin-bottom: 15px;
            }
            .question-type-badge {
                background: #667eea;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }
            .question-text {
                font-size: 1.1rem;
                color: #2d3748;
                margin-bottom: 20px;
                line-height: 1.6;
            }
            .options-container {
                list-style: none;
            }
            .option-item {
                margin-bottom: 12px;
            }
            .option-label {
                display: flex;
                align-items: center;
                padding: 12px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .option-label:hover {
                border-color: #cbd5e0;
                background: #f7fafc;
            }
            .option-label.selected {
                border-color: #667eea;
                background: #ebf8ff;
            }
            .option-radio {
                margin-right: 12px;
                accent-color: #667eea;
            }
            .option-text {
                flex: 1;
                color: #2d3748;
            }
            .submit-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 30px;
                border-top: 2px solid #e2e8f0;
            }
            .submit-section .btn {
                margin: 0 10px;
            }
            .results-section {
                display: none;
            }
            .results-header {
                text-align: center;
                margin-bottom: 30px;
                padding: 30px;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                border-radius: 15px;
            }
            .results-header h2 {
                font-size: 2rem;
                margin-bottom: 10px;
            }
            .score-display {
                font-size: 3rem;
                font-weight: bold;
                margin: 10px 0;
            }
            .score-breakdown {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .score-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .score-card h3 {
                color: #2d3748;
                margin-bottom: 10px;
            }
            .score-card .score-value {
                font-size: 2rem;
                font-weight: bold;
                color: #667eea;
            }
            .review-container {
                margin-top: 30px;
            }
            .review-question {
                background: white;
                border-radius: 10px;
                padding: 25px;
                margin-bottom: 20px;
                border-left: 5px solid #e2e8f0;
            }
            .review-question.correct {
                border-left-color: #48bb78;
            }
            .review-question.incorrect {
                border-left-color: #f56565;
            }
            .review-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            .review-status {
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            .review-status.correct {
                background: #c6f6d5;
                color: #22543d;
            }
            .review-status.incorrect {
                background: #fed7d7;
                color: #742a2a;
            }
            .answer-section {
                margin-top: 15px;
                padding: 15px;
                background: #f7fafc;
                border-radius: 8px;
            }
            .answer-section strong {
                color: #2d3748;
            }
            .correct-answer {
                color: #22543d;
                font-weight: 600;
            }
            .user-answer {
                color: #2d3748;
            }
            .user-answer.incorrect {
                color: #742a2a;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 20px;
                }
                .header h1 {
                    font-size: 2rem;
                }
                .exam-header {
                    flex-direction: column;
                    gap: 15px;
                }
                .exam-info {
                    justify-content: center;
                }
                .question-text {
                    font-size: 1rem;
                }
                .score-breakdown {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📚 MCQ Generator</h1>
                <p>Upload a PDF and take an interactive multiple choice exam</p>
            </div>
            
            <!-- Upload Section -->
            <div class="upload-section" id="uploadSection">
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <div class="upload-icon">📄</div>
                        <div class="upload-text">Click to upload PDF or drag and drop</div>
                        <div class="upload-subtext">Maximum file size: 500MB</div>
                        <input type="file" id="fileInput" name="file" accept=".pdf" required>
                    </div>
                    
                    <div class="file-info" id="fileInfo">
                        <h4>Selected File:</h4>
                        <p id="fileName"></p>
                        <p id="fileSize"></p>
                    </div>
                    
                    <div class="form-group">
                        <label for="numQuestions">Number of MCQ questions:</label>
                        <input type="number" id="numQuestions" name="num_questions" value="5" min="1" max="20">
                    </div>
                    
                    <button type="submit" class="btn btn-primary" id="generateBtn">
                        Generate MCQ Questions & Start Exam
                    </button>
                </form>
                
                <div class="loading" id="loading">
                    <div class="loading-spinner"></div>
                    <p>Processing PDF and generating MCQ questions...</p>
                </div>
                
                <div class="error" id="error"></div>
            </div>
            
            <!-- Exam Section -->
            <div class="exam-section" id="examSection">
                <div class="exam-header">
                    <h2>📝 Take Your MCQ Exam</h2>
                    <div class="exam-info">
                        <div>
                            <span id="questionCount">0 Questions</span>
                        </div>
                        <div class="exam-timer" id="examTimer">Time: 00:00</div>
                        <div>
                            <span id="answeredCount">0 Answered</span>
                        </div>
                    </div>
                </div>
                
                <div class="exam-progress">
                    <div class="exam-progress-bar" id="progressBar"></div>
                </div>
                
                <div id="questionsContainer"></div>
                
                <div class="submit-section">
                    <button class="btn btn-success" id="submitExamBtn" onclick="submitExam()">
                        Submit Exam
                    </button>
                    <button class="btn btn-secondary" onclick="resetExam()">
                        Start Over
                    </button>
                </div>
            </div>
            
            <!-- Results Section -->
            <div class="results-section" id="resultsSection">
                <div class="results-header">
                    <h2>🎉 Exam Results</h2>
                    <div class="score-display" id="finalScore">0/0</div>
                    <p>Congratulations on completing your MCQ exam!</p>
                </div>
                
                <div class="score-breakdown">
                    <div class="score-card">
                        <h3>Total Questions</h3>
                        <div class="score-value" id="totalQuestions">0</div>
                    </div>
                    <div class="score-card">
                        <h3>Correct Answers</h3>
                        <div class="score-value" id="correctAnswers">0</div>
                    </div>
                    <div class="score-card">
                        <h3>Accuracy</h3>
                        <div class="score-value" id="accuracyPercentage">0%</div>
                    </div>
                    <div class="score-card">
                        <h3>Time Taken</h3>
                        <div class="score-value" id="timeTaken">0:00</div>
                    </div>
                </div>
                
                <div class="review-container">
                    <h3 style="margin-bottom: 20px; color: #2d3748;">📋 Question Review</h3>
                    <div id="reviewContainer"></div>
                </div>
                
                <div class="submit-section">
                    <button class="btn btn-primary" onclick="resetExam()">
                        Generate New Questions
                    </button>
                </div>
            </div>
        </div>

        <script>
            let currentQuestions = [];
            let userAnswers = {};
            let examStartTime = null;
            let examTimer = null;
            
            // File handling
            const fileInput = document.getElementById('fileInput');
            const uploadArea = document.querySelector('.upload-area');
            const fileInfo = document.getElementById('fileInfo');
            const fileName = document.getElementById('fileName');
            const fileSize = document.getElementById('fileSize');
            const uploadForm = document.getElementById('uploadForm');
            const generateBtn = document.getElementById('generateBtn');
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');

            fileInput.addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    showFileInfo(file);
                }
            });

            uploadArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0 && files[0].type === 'application/pdf') {
                    fileInput.files = files;
                    showFileInfo(files[0]);
                }
            });

            function showFileInfo(file) {
                fileName.textContent = file.name;
                fileSize.textContent = `Size: ${(file.size / 1024 / 1024).toFixed(2)} MB`;
                fileInfo.style.display = 'block';
            }

            // Form submission
            uploadForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData();
                const file = fileInput.files[0];
                const numQuestions = document.getElementById('numQuestions').value;
                
                if (!file) {
                    showError('Please select a PDF file');
                    return;
                }
                
                formData.append('file', file);
                formData.append('num_questions', numQuestions);
                
                generateBtn.disabled = true;
                loading.style.display = 'block';
                error.style.display = 'none';
                
                try {
                    const response = await fetch('/generate_questions_from_pdf', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        currentQuestions = result.questions;
                        startExam();
                    } else {
                        showError(result.message || 'Failed to generate questions');
                    }
                } catch (err) {
                    showError('Network error: ' + err.message);
                } finally {
                    generateBtn.disabled = false;
                    loading.style.display = 'none';
                }
            });

            function startExam() {
                document.getElementById('uploadSection').style.display = 'none';
                document.getElementById('examSection').style.display = 'block';
                document.getElementById('resultsSection').style.display = 'none';
                
                userAnswers = {};
                examStartTime = new Date();
                
                document.getElementById('questionCount').textContent = `${currentQuestions.length} Questions`;
                document.getElementById('answeredCount').textContent = '0 Answered';
                
                displayExamQuestions();
                startExamTimer();
            }
            
            function displayExamQuestions() {
                const container = document.getElementById('questionsContainer');
                container.innerHTML = '';
                
                currentQuestions.forEach((question, index) => {
                    const questionDiv = document.createElement('div');
                    questionDiv.className = 'question-container';
                    
                    const optionsList = question.options.map((option, i) => {
                        const optionId = `q${index}_option${i}`;
                        return `
                            <li class="option-item">
                                <label class="option-label" for="${optionId}">
                                    <input type="radio" 
                                           class="option-radio" 
                                           id="${optionId}"
                                           name="question_${index}" 
                                           value="${option}" 
                                           onchange="updateAnswer(${index}, '${option}', this)">
                                    <span class="option-text">${String.fromCharCode(65 + i)}. ${option}</span>
                                </label>
                            </li>
                        `;
                    }).join('');
                    
                    questionDiv.innerHTML = `
                        <div class="question-number">
                            Question ${index + 1} of ${currentQuestions.length}
                            <span class="question-type-badge">MCQ</span>
                        </div>
                        <div class="question-text">${question.question}</div>
                        <ul class="options-container">${optionsList}</ul>
                    `;
                    
                    container.appendChild(questionDiv);
                });
                
                updateProgress();
            }
            
            function updateAnswer(questionIndex, answer, radioElement) {
                userAnswers[questionIndex] = answer;
                
                // Update visual selection
                const questionContainer = radioElement.closest('.question-container');
                const labels = questionContainer.querySelectorAll('.option-label');
                labels.forEach(label => label.classList.remove('selected'));
                radioElement.closest('.option-label').classList.add('selected');
                
                updateProgress();
            }
            
            function updateProgress() {
                const answered = Object.keys(userAnswers).filter(key => {
                    const answer = userAnswers[key];
                    return answer && answer.toString().trim() !== '';
                }).length;
                const total = currentQuestions.length;
                const percentage = (answered / total) * 100;
                
                document.getElementById('progressBar').style.width = percentage + '%';
                document.getElementById('answeredCount').textContent = `${answered} Answered`;
            }
            
            function startExamTimer() {
                examTimer = setInterval(() => {
                    const now = new Date();
                    const elapsed = Math.floor((now - examStartTime) / 1000);
                    const minutes = Math.floor(elapsed / 60);
                    const seconds = elapsed % 60;
                    document.getElementById('examTimer').textContent = 
                        `Time: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                }, 1000);
            }
            
            function submitExam() {
                if (examTimer) {
                    clearInterval(examTimer);
                }
                
                const examEndTime = new Date();
                const totalTime = Math.floor((examEndTime - examStartTime) / 1000);
                
                // Calculate results
                let correctCount = 0;
                const results = [];
                
                currentQuestions.forEach((question, index) => {
                    const userAnswer = userAnswers[index] || '';
                    const isCorrect = userAnswer === question.answer;
                    
                    if (isCorrect) {
                        correctCount++;
                    }
                    
                    results.push({
                        question: question,
                        userAnswer: userAnswer,
                        correctAnswer: question.answer,
                        isCorrect: isCorrect
                    });
                });
                
                displayResults(correctCount, totalTime, results);
            }
            
            function displayResults(correctCount, totalTime, results) {
                document.getElementById('uploadSection').style.display = 'none';
                document.getElementById('examSection').style.display = 'none';
                document.getElementById('resultsSection').style.display = 'block';
                
                const total = currentQuestions.length;
                const accuracy = Math.round((correctCount / total) * 100);
                const minutes = Math.floor(totalTime / 60);
                const seconds = totalTime % 60;
                
                // Update score display
                document.getElementById('finalScore').textContent = `${correctCount}/${total}`;
                document.getElementById('totalQuestions').textContent = total;
                document.getElementById('correctAnswers').textContent = correctCount;
                document.getElementById('accuracyPercentage').textContent = `${accuracy}%`;
                document.getElementById('timeTaken').textContent = 
                    `${minutes}:${seconds.toString().padStart(2, '0')}`;
                
                // Display question review
                displayQuestionReview(results);
            }
            
            function displayQuestionReview(results) {
                const container = document.getElementById('reviewContainer');
                container.innerHTML = '';
                
                results.forEach((result, index) => {
                    const reviewDiv = document.createElement('div');
                    const isCorrect = result.isCorrect;
                    const reviewClass = isCorrect ? 'correct' : 'incorrect';
                    const statusText = isCorrect ? '✅ Correct' : '❌ Incorrect';
                    
                    const answerSection = `
                        <div class="answer-section">
                            <strong>Your Answer:</strong> 
                            <span class="user-answer ${isCorrect ? '' : 'incorrect'}">${result.userAnswer || 'No answer'}</span><br>
                            <strong>Correct Answer:</strong> 
                            <span class="correct-answer">${result.correctAnswer}</span>
                        </div>
                    `;
                    
                    reviewDiv.className = `review-question ${reviewClass}`;
                    reviewDiv.innerHTML = `
                        <div class="review-header">
                            <div class="question-number">Question ${index + 1} (MCQ)</div>
                            <div class="review-status ${reviewClass}">
                                ${statusText}
                            </div>
                        </div>
                        <div class="question-text">${result.question.question}</div>
                        ${answerSection}
                    `;
                    
                    container.appendChild(reviewDiv);
                });
            }
                
            function resetExam() {
                document.getElementById('uploadSection').style.display = 'block';
                document.getElementById('examSection').style.display = 'none';
                document.getElementById('resultsSection').style.display = 'none';
                
                currentQuestions = [];
                userAnswers = {};
                
                if (examTimer) {
                    clearInterval(examTimer);
                }
                
                // Reset form
                document.getElementById('uploadForm').reset();
                fileInfo.style.display = 'none';
                error.style.display = 'none';
            }

            function showError(message) {
                error.textContent = message;
                error.style.display = 'block';
                error.scrollIntoView({ behavior: 'smooth' });
            }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/generate_questions_from_pdf', methods=['POST'])
def generate_questions_from_pdf():
    """Generate MCQs from PDF file"""
    try:
        # Check if spaCy is available
        if not is_spacy_available():
            return jsonify({
                'success': False,
                'error': 'NLP model not available',
                'message': 'spaCy English model is not loaded. Please install it with: python -m spacy download en_core_web_sm'
            }), 503
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'message': 'Please upload a PDF file'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'message': 'Please select a PDF file to upload'
            }), 400
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'message': 'Only PDF files are supported'
            }), 400
        
        # Get parameters
        num_questions = request.form.get('num_questions', 5)
        
        try:
            num_questions = int(num_questions)
            if num_questions < 1 or num_questions > 20:
                raise ValueError()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid number of questions',
                'message': 'num_questions must be an integer between 1 and 20'
            }), 400
        
        logger.info(f"Processing PDF file: {file.filename}")
        
        # Extract text from PDF
        try:
            pdf_reader = PyPDF2.PdfReader(file.stream)
            text = ""
            pages_processed = 0
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"
                        pages_processed += 1
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            if not text.strip():
                return jsonify({
                    'success': False,
                    'error': 'No text extracted',
                    'message': 'Could not extract readable text from the PDF file'
                }), 422
            
            logger.info(f"Extracted text from {pages_processed} pages, total length: {len(text)}")
            
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'PDF processing error',
                'message': 'Could not read the PDF file. Please ensure it is not corrupted.'
            }), 422
        
        # Generate MCQs
        start_time = datetime.now()
        mcqs = generate_mcqs(text, num_questions)
        
        # Add type field to each question
        for mcq in mcqs:
            mcq['type'] = 'mcq'
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        if not mcqs:
            return jsonify({
                'success': False,
                'error': 'No questions generated',
                'message': 'Could not generate MCQ questions from the PDF content. The document may not contain enough suitable information.'
            }), 422
        
        # Shuffle questions for variety
        import random
        random.shuffle(mcqs)
        
        logger.info(f"Successfully generated {len(mcqs)} MCQ questions from PDF in {processing_time:.2f}s")
        
        return jsonify({
            'success': True,
            'questions': mcqs,
            'processing_time': processing_time,
            'pages_processed': pages_processed,
            'text_length': len(text)
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_questions_from_pdf: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Processing error',
            'message': 'An unexpected error occurred while processing your request'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
