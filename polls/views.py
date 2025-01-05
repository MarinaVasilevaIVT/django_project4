from django.db.models import F, Sum
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.urls import reverse
from django.views import View, generic
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout

from .models import Choice, Question
from .forms import PollForm 

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"
    
    def get_queryset(self):
        # Возвращает последние пять опубликованных вопроса
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

class StatisticsView(View):
    def get(self, request, *args, **kwargs):
        context = {'message': 'Привет, это GET-запрос!'}
        return render(request, 'polls/statistics.html', context)

    def post(self, request, *args, **kwargs):
        context = {'message': 'Привет, это POST-запрос!'}
        return render(request, 'polls/statistics.html', context)

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))

@login_required
def create_poll(request):
    if request.method == 'POST':
        form = PollForm(request.POST)
        if form.is_valid():
            # Сохраняем вопрос
            question = form.save(commit=False)
            question.pub_date = timezone.now() 
            question.save()
            
            # Получаем варианты ответов
            choices = request.POST.get('choices').splitlines()
            for choice_text in choices:
                if choice_text.strip(): 
                    Choice.objects.create(question=question, choice_text=choice_text.strip())
            return redirect('polls:index')
    else:
        form = PollForm()
    return render(request, 'polls/create_poll.html', {'form': form})

# Представление для регистрации
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('polls:index')
    else:
        form = UserCreationForm()
    return render(request, 'polls/register.html', {'form': form})

# Представление для входа
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('polls:index')
    else:
        form = AuthenticationForm()
    return render(request, 'polls/login.html', {'form': form})

# Представление для выхода
def logout_view(request):
    logout(request)
    return redirect('polls:index')


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import parsers, status
from datetime import datetime, timedelta
from django.utils import timezone
from .serializers import QuestionSerializer
from .models import Question

class QuestionView(APIView):
    parser_classes = (parsers.JSONParser,)

    def post(self, request, format=None):
        request_data = request.data

        # Получение интервала дат
        date_range_provided = ('publication-dates' in request_data) and \
                              ('from' in request_data['publication-dates'] and 'to' in request_data['publication-dates'])
        
        if date_range_provided:
            publication_dates = request_data['publication-dates']
            date_from = datetime.strptime(publication_dates['from'], '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            date_to = datetime.strptime(publication_dates['to'], '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        else:
            date_now = timezone.now()
            date_from = (date_now - timedelta(days=60)).replace(hour=0, minute=0, second=0)
            date_to = date_now.replace(hour=23, minute=59, second=59)

        # Получение диапазона голосов
        votes_range = request_data.get('votes-range', {})
        min_votes = votes_range.get('min', 0)  # По умолчанию 0
        max_votes = votes_range.get('max', float('inf'))  # По умолчанию бесконечность

        # Фильтрация вопросов по дате и количеству голосов
        questions = Question.objects.filter(pub_date__range=[date_from, date_to])
        questions = questions.annotate(total_votes=Sum('choice__votes')).filter(
            total_votes__gte=min_votes,
            total_votes__lte=max_votes
        )

        # Сериализация данных
        question_serializer = QuestionSerializer(questions, many=True)
        
        response_data = {
            'publication-dates': {
                'from': date_from,
                'to': date_to
            },
            'questions': question_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)

from django.utils import timezone
from django.http import JsonResponse
from django.contrib import admin

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Question, Choice

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Используем бэкенд для сохранения изображений без GUI
import io


class QuestionStatsAPIView(APIView):
    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return Response("Question does not exist", status=status.HTTP_404_NOT_FOUND)

        choices = question.choice_set.all()
        total_votes = sum(choice.votes for choice in choices)

        stats = {
            'question': question.question_text,
            'total_votes': total_votes,
            'choices': []
        }

        for choice in choices:
            choice_percentage = (choice.votes / total_votes) * 100 if total_votes != 0 else 0
            stats['choices'].append({
                'choice_text': choice.choice_text,
                'votes': choice.votes,
                'percentage': round(choice_percentage, 2)
            })

        most_popular_choice = max(choices, key=lambda choice: choice.votes)
        least_popular_choice = min(choices, key=lambda choice: choice.votes)

        stats['most_popular_choice'] = most_popular_choice.choice_text
        stats['least_popular_choice'] = least_popular_choice.choice_text

        fig, ax = plt.subplots()
        plt.style.use('ggplot')
        ax.bar([choice.choice_text for choice in choices], [choice.votes for choice in choices])
        plt.xticks(rotation=20)
        plt.xlabel('Choices')
        plt.ylabel('Votes')
        plt.title('Votes Distribution')
        plt.subplots_adjust(bottom=0.2)
        buffer = io.BytesIO()
        plt.savefig(buffer, format='svg')
        plt.close(fig)
        buffer.seek(0)

        stats['histogram_svg'] = buffer.getvalue().decode()

        return Response(stats)

import csv
from django.http import HttpResponse

class ExportDataView(APIView):
    def get(self, request, format=None):
        questions = Question.objects.all()
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="polls_data.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Question', 'Choice', 'Votes'])
        
        for question in questions:
            for choice in question.choice_set.all():
                writer.writerow([question.question_text, choice.choice_text, choice.votes])
        
        return response