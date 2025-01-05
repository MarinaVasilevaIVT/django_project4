from rest_framework import serializers
from .models import Question


class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    
    class Meta:
        model = Question
        fields = '__all__'
