from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from datetime import datetime
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///insurance.db'
db = SQLAlchemy(app)

# Define upload folder as absolute path
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class InsuranceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_officer = db.Column(db.String(100), nullable=False)
    hospital_name = db.Column(db.String(200), nullable=False)
    hospital_id = db.Column(db.String(50), nullable=False)
    case_id = db.Column(db.String(50), nullable=False)
    procedure_id = db.Column(db.String(50), nullable=False)
    pmjay_card = db.Column(db.String(50), nullable=False)
    date_admission = db.Column(db.Date, nullable=False)
    expenditure = db.Column(db.Float, nullable=False)
    fraud_type = db.Column(db.String(100))
    photo_path = db.Column(db.String(200))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Handle photo upload
        if 'photo' not in request.files:
            flash('No photo uploaded', 'error')
            return redirect(url_for('index'))
            
        photo = request.files['photo']
        if photo.filename == '':
            flash('No photo selected', 'error')
            return redirect(url_for('index'))
            
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            # Use field officer name in filename
            field_officer = request.form['field_officer'].replace(' ', '_')
            extension = filename.rsplit('.', 1)[1].lower()
            filename = f"{field_officer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
            
            # Save file to uploads directory
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Create record with photo path
            record = InsuranceRecord(
                field_officer=request.form['field_officer'],
                hospital_name=request.form['hospital_name'],
                hospital_id=request.form['hospital_id'],
                case_id=request.form['case_id'],
                procedure_id=request.form['procedure_id'],
                pmjay_card=request.form['pmjay_card'],
                date_admission=datetime.strptime(request.form['date_admission'], '%Y-%m-%d'),
                expenditure=float(request.form['expenditure']),
                fraud_type=request.form['fraud_type'],
                photo_path='uploads/' + filename
            )
            db.session.add(record)
            db.session.commit()
            flash('Record added successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Only PNG, JPG, and JPEG files are allowed.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/view')
def view_records():
    records = InsuranceRecord.query.all()
    return render_template('view_records.html', records=records)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_record(id):
    record = InsuranceRecord.query.get_or_404(id)
    if request.method == 'POST':
        try:
            # Handle photo upload if new photo is provided
            if 'photo' in request.files and request.files['photo'].filename != '':
                photo = request.files['photo']
                if photo and allowed_file(photo.filename):
                    # Delete old photo if it exists
                    if record.photo_path:
                        old_photo_path = os.path.join(app.root_path, 'static', record.photo_path)
                        if os.path.exists(old_photo_path):
                            os.remove(old_photo_path)
                    
                    # Save new photo with field officer name
                    filename = secure_filename(photo.filename)
                    field_officer = request.form['field_officer'].replace(' ', '_')
                    extension = filename.rsplit('.', 1)[1].lower()
                    filename = f"{field_officer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
                    
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    photo.save(photo_path)
                    record.photo_path = os.path.join('uploads', filename)
                else:
                    flash('Invalid file type. Only PNG, JPG, and JPEG files are allowed.', 'error')
                    return redirect(url_for('edit_record', id=id))

            # Update other fields
            record.field_officer = request.form['field_officer']
            record.hospital_name = request.form['hospital_name']
            record.hospital_id = request.form['hospital_id']
            record.case_id = request.form['case_id']
            record.procedure_id = request.form['procedure_id']
            record.pmjay_card = request.form['pmjay_card']
            record.date_admission = datetime.strptime(request.form['date_admission'], '%Y-%m-%d')
            record.expenditure = float(request.form['expenditure'])
            record.fraud_type = request.form['fraud_type']
            
            db.session.commit()
            flash('Record updated successfully!', 'success')
            return redirect(url_for('view_records'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('edit_record', id=id))
    return render_template('edit_record.html', record=record)

@app.route('/delete/<int:id>')
def delete_record(id):
    record = InsuranceRecord.query.get_or_404(id)
    try:
        # Delete photo file if it exists
        if record.photo_path:
            photo_path = os.path.join(app.root_path, 'static', record.photo_path)
            if os.path.exists(photo_path):
                os.remove(photo_path)
                
        db.session.delete(record)
        db.session.commit()
        flash('Record deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    return redirect(url_for('view_records'))

@app.route('/download')
def download_excel():
    records = InsuranceRecord.query.all()
    data = []
    for record in records:
        data.append({
            'Field Officer': record.field_officer,
            'Hospital Name': record.hospital_name,
            'Hospital ID': record.hospital_id,
            'Case ID': record.case_id,
            'Procedure ID': record.procedure_id,
            'PMJAY Card': record.pmjay_card,
            'Date of Admission': record.date_admission,
            'Expenditure': record.expenditure,
            'Fraud Type': record.fraud_type,
            'Photo Link': record.photo_path if record.photo_path else 'No photo'
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Insurance Records')
        worksheet = writer.sheets['Insurance Records']
        workbook = writer.book

        # Create header format
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#D9D9D9',
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center'
        })
        
        # Auto-adjust columns width and apply header format
        for idx, col in enumerate(df.columns):
            series = df[col]
            max_len = max(
                series.astype(str).map(len).max(),
                len(str(series.name))
            ) + 1
            worksheet.set_column(idx, idx, max_len)
            worksheet.write(0, idx, col, header_format)
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='insurance_records.xlsx'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 
   