import re
import os
from collections import defaultdict

class StudentResult:
    def __init__(self, symbol_number, name, roll_no, subjects, total_marks, obtained_marks, result):
        self.symbol_number = symbol_number
        self.name = name
        self.roll_no = roll_no
        self.subjects = subjects
        self.total_marks = total_marks
        self.obtained_marks = obtained_marks
        self.result = result
    
    def get_failed_subjects(self):
        return [subj for subj, marks in self.subjects.items() 
                if marks[2] is not None and marks[2] < marks[1]]

def get_text_files():
    """Get all .txt files in current directory"""
    files = [f for f in os.listdir() if f.endswith('.txt')]
    return files

def select_file(files):
    """Let user select a file from the list"""
    if not files:
        print("No .txt files found in current directory.")
        return None
    
    print("\nAvailable text files:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    
    while True:
        try:
            choice = int(input("\nEnter the number of file to analyze (0 to exit): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(files):
                return files[choice-1]
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

def parse_results_file(filename):
    students = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except UnicodeDecodeError:
        try:
            with open(filename, 'r', encoding='latin-1') as file:
                content = file.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return []
    
    student_records = re.split(r'=+\s*Results for Symbol Number:\s*\d+\s*=+', content)[1:]
    
    if not student_records:
        student_records = re.split(r'=+\s*Results for\s*Symbol Number:\s*\d+\s*=+', content)[1:]
    
    for record in student_records:
        try:
            symbol_match = re.search(r'Symbol Number:\s*(\d+)', record)
            symbol_number = symbol_match.group(1) if symbol_match else "Unknown"
            
            name_match = re.search(r'NAME:\s*(.+?)\s*$', record, re.MULTILINE)
            name = name_match.group(1).strip() if name_match else "Unknown"
            
            roll_match = re.search(r'ROLL NO:\s*(\d+)', record)
            roll_no = roll_match.group(1) if roll_match else "Unknown"
            
            subjects = {}
            subject_lines = re.findall(r'^([A-Za-z]+\s*\d+:.+?)\s+(\d+)\s+(\d+\.?\d*)\s+(\d*\.?\d*)', record, re.MULTILINE)
            
            for subj_line in subject_lines:
                subject_code = subj_line[0].strip()
                full_marks = float(subj_line[1])
                pass_marks = float(subj_line[2])
                obtained = float(subj_line[3]) if subj_line[3] else None
                subjects[subject_code] = (full_marks, pass_marks, obtained)
            
            total_match = re.search(r'Total Marks:\s*(\d+)', record)
            total_marks = float(total_match.group(1)) if total_match else 0
            
            obtained_match = re.search(r'Obtained.*Marks:\s*(\d+)', record)
            obtained_marks = float(obtained_match.group(1)) if obtained_match else 0
            
            result_match = re.search(r'Result:\s*(\w+)', record)
            result = result_match.group(1) if result_match else "Unknown"
            
            if subjects:
                student = StudentResult(symbol_number, name, roll_no, subjects, 
                                      total_marks, obtained_marks, result)
                students.append(student)
        
        except Exception as e:
            print(f"Error processing record: {e}")
            continue
    
    return students

def analyze_results(students):
    analysis = {
        'total_students': len(students),
        'passed_students': sum(1 for s in students if s.result == 'P'),
        'failed_students': sum(1 for s in students if s.result == 'F'),
        'pass_percentage': 0,
        'subject_analysis': defaultdict(lambda: {
            'total_attempts': 0,
            'passes': 0,
            'failures': 0,
            'highest': 0,
            'lowest': float('inf'),
            'average': 0,
            'total_marks': 0
        }),
        'top_students': [],
        'weak_subjects': defaultdict(int)
    }
    
    if analysis['total_students'] > 0:
        analysis['pass_percentage'] = (analysis['passed_students'] / analysis['total_students']) * 100
    
    for student in students:
        for subj, marks in student.subjects.items():
            if marks[2] is not None:
                subj_analysis = analysis['subject_analysis'][subj]
                subj_analysis['total_attempts'] += 1
                subj_analysis['total_marks'] += marks[2]
                
                if marks[2] >= marks[1]:
                    subj_analysis['passes'] += 1
                else:
                    subj_analysis['failures'] += 1
                    analysis['weak_subjects'][subj] += 1
                
                if marks[2] > subj_analysis['highest']:
                    subj_analysis['highest'] = marks[2]
                if marks[2] < subj_analysis['lowest']:
                    subj_analysis['lowest'] = marks[2]
    
    for subj, data in analysis['subject_analysis'].items():
        if data['total_attempts'] > 0:
            data['average'] = data['total_marks'] / data['total_attempts']
    
    passed_students = [s for s in students if s.result == 'P']
    passed_students.sort(key=lambda x: x.obtained_marks, reverse=True)
    analysis['top_students'] = passed_students[:3]
    
    analysis['weak_subjects'] = sorted(analysis['weak_subjects'].items(), 
                                     key=lambda x: x[1], reverse=True)
    
    return analysis

def display_analysis(analysis):
    print("\n=== Overall Results Analysis ===")
    print(f"Total Students: {analysis['total_students']}")
    print(f"Passed Students: {analysis['passed_students']}")
    print(f"Failed Students: {analysis['failed_students']}")
    print(f"Pass Percentage: {analysis['pass_percentage']:.2f}%")
    
    print("\n=== Subject-wise Analysis ===")
    for subj, data in analysis['subject_analysis'].items():
        pass_rate = (data['passes'] / data['total_attempts'] * 100) if data['total_attempts'] > 0 else 0
        print(f"\nSubject: {subj}")
        print(f"  Total Attempts: {data['total_attempts']}")
        print(f"  Passes: {data['passes']} ({pass_rate:.2f}%)")
        print(f"  Failures: {data['failures']}")
        print(f"  Highest Marks: {data['highest']}")
        print(f"  Lowest Marks: {data['lowest']}")
        print(f"  Average Marks: {data['average']:.2f}")
    
    print("\n=== Top Performing Students ===")
    for i, student in enumerate(analysis['top_students'], 1):
        print(f"{i}. {student.name} (Roll No: {student.roll_no}) - {student.obtained_marks} marks")
    
    print("\n=== Most Challenging Subjects ===")
    for subj, failures in analysis['weak_subjects'][:5]:
        print(f"{subj}: {failures} failures")

def main():
    print("Student Results Analyzer")
    print("=======================")
    
    files = get_text_files()
    selected_file = select_file(files)
    
    if not selected_file:
        return
    
    print(f"\nAnalyzing file: {selected_file}")
    students = parse_results_file(selected_file)
    
    if not students:
        print("No student data found in the file.")
        return
    
    analysis = analyze_results(students)
    display_analysis(analysis)

if __name__ == "__main__":
    main()
