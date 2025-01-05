from django import forms
from .models import Question

class PollForm(forms.ModelForm):
    choices = forms.CharField(widget=forms.Textarea, help_text="Каждый вариант на отдельной строке.")
    
    class Meta:
        model = Question
        fields = ['question_text', 'choices']
