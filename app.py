import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

# --- Configuration ---
UPLOAD_FOLDER = 'uploads' # Optional: Define a folder to store uploads
ALLOWED_EXTENSIONS = {'txt'} # Initially allow only text files for simplicity

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'your_super_secret_key' # Change this for production!
# Optional: Create the uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    # os.makedirs(UPLOAD_FOLDER)

# --- Helper Functions ---

def allowed_file(filename):
    """Checks if the uploaded file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def simulate_ai_extraction(text):
    """
    SIMULATES AI Data Extraction using basic Regex.
    In a real system, this would use a trained NLP/ML model.
    """
    extracted_data = {}
    # Example patterns (very basic - improve significantly for real use)
    patterns = {
        'counterparty': r"Counterparty:\s*(.+)",
        'trade_date': r"Trade Date:\s*(\d{4}-\d{2}-\d{2})", # YYYY-MM-DD
        'notional_amount': r"Notional Amount:\s*([\d,]+\.?\d*)",
        'currency': r"Currency:\s*([A-Z]{3})",
        'maturity_date': r"Maturity Date:\s*(\d{4}-\d{2}-\d{2})", # YYYY-MM-DD
        'product_type': r"Product Type:\s*(.+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_data[key] = match.group(1).strip()
        else:
            extracted_data[key] = None # Indicate field not found

    # Basic cleanup for amount
    if extracted_data.get('notional_amount'):
        extracted_data['notional_amount'] = extracted_data['notional_amount'].replace(',', '')

    print(f"DEBUG: Extracted Data: {extracted_data}") # For debugging
    return extracted_data

def simulate_ai_validation(data):
    """
    SIMULATES AI Validation based on predefined criteria.
    In a real system, this could involve ML models or complex rule engines.
    """
    validation_results = {}
    # Example Validation Rules
    required_fields = ['counterparty', 'trade_date', 'notional_amount', 'currency', 'maturity_date']

    for field in data:
        is_valid = True
        message = "Valid"
        value = data[field]

        # 1. Check if required fields are present
        if field in required_fields and value is None:
            is_valid = False
            message = "Required field missing."
        # 2. Basic format checks (add more!)
        elif field in ['trade_date', 'maturity_date'] and value:
            # Simple date format check (can use datetime for stricter check)
            if not re.match(r"\d{4}-\d{2}-\d{2}", value):
                 is_valid = False
                 message = "Invalid date format (expected YYYY-MM-DD)."
        elif field == 'notional_amount' and value:
            try:
                float(value) # Check if it's convertible to a number
                if float(value) <= 0:
                    is_valid = False
                    message = "Notional Amount must be positive."
            except ValueError:
                is_valid = False
                message = "Notional Amount is not a valid number."
        elif field == 'currency' and value:
             if not re.match(r"^[A-Z]{3}$", value):
                 is_valid = False
                 message = "Invalid currency format (expected 3 uppercase letters)."

        # Add more complex rules: e.g., maturity date > trade date, check against reference data, etc.

        validation_results[field] = {
            'value': value,
            'valid': is_valid,
            'message': message
        }

    print(f"DEBUG: Validation Results: {validation_results}") # For debugging
    return validation_results

def extract_text_from_file(filepath):
    """Extracts text from allowed file types."""
    # Basic TXT handling
    if filepath.lower().endswith('.txt'):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file {filepath}: {e}")
            return None
    # Placeholder for other types
    # elif filepath.lower().endswith('.pdf'):
    #     # Add PyPDF2 logic here
    #     return "PDF parsing not implemented yet."
    # elif filepath.lower().endswith('.docx'):
    #     # Add python-docx logic here
    #     return "DOCX parsing not implemented yet."
    else:
        return None

# --- Flask Routes ---

@app.route('/', methods=['GET'])
def index():
    """Displays the main form for text input or file upload."""
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate_termsheet():
    """Handles form submission, performs extraction and validation."""
    term_sheet_text = None
    original_filename = None

    # Check if text was submitted directly
    if 'term_sheet_text' in request.form and request.form['term_sheet_text'].strip():
        term_sheet_text = request.form['term_sheet_text']
        print("DEBUG: Processing text input.")

    # Check if a file was uploaded
    elif 'term_sheet_file' in request.files:
        file = request.files['term_sheet_file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            original_filename = filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(filepath)
                print(f"DEBUG: File saved to {filepath}")
                term_sheet_text = extract_text_from_file(filepath)
                if term_sheet_text is None:
                     flash(f'Could not extract text from file: {filename}')
                     return redirect(url_for('index'))
                print(f"DEBUG: Extracted text from file {filename}.")
                # Optional: Delete file after processing if not needed
                # os.remove(filepath)
            except Exception as e:
                flash(f'Error processing file: {e}')
                print(f"ERROR: saving or processing file {filename}: {e}")
                return redirect(url_for('index'))

        elif file and not allowed_file(file.filename):
            flash(f'File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}')
            return redirect(url_for('index'))

    # If we have text (from input or file), process it
    if term_sheet_text:
        # Simulate AI Steps
        extracted_data = simulate_ai_extraction(term_sheet_text)
        validation_results = simulate_ai_validation(extracted_data)

        # Render results page
        return render_template('results.html',
                               validation=validation_results,
                               original_text=term_sheet_text[:1000]+"..." # Show snippet
                               )
    else:
        # No input provided
        flash('Please enter term sheet text or upload a valid file.')
        return redirect(url_for('index'))

# --- Run the Application ---
if __name__ == '__main__':
    app.run(debug=True) # Debug=True for development, set to False for production