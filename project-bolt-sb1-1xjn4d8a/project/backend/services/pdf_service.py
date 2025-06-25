from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from typing import Dict, Any
from database.models import CompletePlan
from datetime import datetime

class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2563eb')
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#1f2937')
        ))
        
        self.styles.add(ParagraphStyle(
            name='WorkoutDay',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor('#059669')
        ))
    
    def generate_plan_pdf(self, plan: CompletePlan) -> bytes:
        """Generate PDF for a complete plan"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        story = []
        
        # Title page
        self._add_title_page(story, plan)
        story.append(PageBreak())
        
        # Plan overview
        self._add_plan_overview(story, plan)
        story.append(PageBreak())
        
        # 4-week workout plan
        self._add_workout_plan(story, plan)
        story.append(PageBreak())
        
        # Nutrition plan
        self._add_nutrition_plan(story, plan)
        story.append(PageBreak())
        
        # Progress tracking section
        self._add_progress_tracking(story, plan)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _add_title_page(self, story, plan: CompletePlan):
        """Add title page to PDF"""
        story.append(Spacer(1, 2*inch))
        
        title = Paragraph("4-Week Personalized Training & Nutrition Plan", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # User info
        created_date = plan.created_at.strftime('%B %d, %Y') if hasattr(plan.created_at, 'strftime') else str(plan.created_at)[:10]
        
        user_info = f"""
        <b>Name:</b> {plan.profile_snapshot.full_name}<br/>
        <b>Goal:</b> {plan.profile_snapshot.primary_fitness_goal.value.replace('_', ' ').title()}<br/>
        <b>Training Days:</b> {plan.profile_snapshot.preferred_training_days} days per week<br/>
        <b>Experience Level:</b> {plan.profile_snapshot.gym_experience.value.title()}<br/>
        <b>Plan Created:</b> {created_date}
        """
        
        user_para = Paragraph(user_info, self.styles['Normal'])
        story.append(user_para)
        story.append(Spacer(1, 1*inch))
        
        # Important notes
        notes = """
        <b>Important Notes:</b><br/>
        • Follow the plan for 4 consecutive weeks<br/>
        • Rest 1-2 days between workouts<br/>
        • Focus on proper form over heavy weights<br/>
        • Stay hydrated and get adequate sleep<br/>
        • Consult a healthcare provider before starting any new exercise program
        """
        
        notes_para = Paragraph(notes, self.styles['Normal'])
        story.append(notes_para)
    
    def generate_simple_plan_pdf(self, plan_data: Dict[str, Any]) -> bytes:
        """Generate PDF for simple plan format (legacy support)"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph("Personalized Fitness Plan", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Workout Plan
        story.append(Paragraph("Workout Plan", self.styles['SectionHeader']))
        
        if 'workout_plan' in plan_data:
            for day in plan_data['workout_plan']:
                # Day header
                day_title = f"{day['day']} - {', '.join(day['muscle_groups']).title()}"
                story.append(Paragraph(day_title, self.styles['WorkoutDay']))
                
                # Exercise table
                exercise_data = [['Exercise', 'Sets', 'Reps', 'Rest']]
                for ex in day['exercises']:
                    exercise_data.append([
                        ex['name'],
                        str(ex['sets']),
                        ex['reps'],
                        f"{ex['rest_seconds']}s"
                    ])
                
                exercise_table = Table(exercise_data)
                exercise_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(exercise_table)
                story.append(Spacer(1, 0.3*inch))
        
        story.append(PageBreak())
        
        # Nutrition Plan
        story.append(Paragraph("Nutrition Plan", self.styles['SectionHeader']))
        
        if 'nutrition_plan' in plan_data:
            nutrition = plan_data['nutrition_plan']
            
            # Daily targets
            targets_data = [
                ['Nutrient', 'Daily Target'],
                ['Calories', f"{nutrition['daily_targets']['calories']} kcal"],
                ['Protein', f"{nutrition['daily_targets']['protein_g']}g"],
                ['Carbs', f"{nutrition['daily_targets']['carbs_g']}g"],
                ['Fat', f"{nutrition['daily_targets']['fat_g']}g"]
            ]
            
            targets_table = Table(targets_data)
            targets_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(targets_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
