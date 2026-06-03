from django.shortcuts import render
from .models import DemandData
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime


def serialize_demand_data(item):
    return {
        'id': item.id,
        'date': item.date.isoformat() if item.date else None,
        'time_block': item.time_block,
        'current_demand': item.current_demand,
        'yesterday_demand': item.yesterday_demand,
        'captured_at': item.captured_at.isoformat(),
    }

# This view renders the initial HTML page
def show_all_data_homepage(request):
    """
    This view now ONLY renders the initial page structure.
    The data will be loaded via AJAX.
    """
    return render(request, 'data_capture/latest_data.html')

# This view provides the latest data as a JSON object
def latest_data_json(request):
    """
    This view provides the latest data as a JSON object, which will be
    fetched by the JavaScript on the frontend.
    """
    recent_data_qs = DemandData.objects.order_by('-captured_at')[:48]
    recent_data = list(recent_data_qs)[::-1] 

    if not recent_data:
        return JsonResponse({'error': 'No data available'}, status=404)

    labels = []
    current_demand_data = []
    yesterday_demand_data = []
    time_between_captures = [0] 

    for i in range(len(recent_data)):
        item = recent_data[i]
        labels.append(item.time_block or item.captured_at.strftime('%H:%M'))
        
        try:
            # === FINAL FIX: Clean the string thoroughly before converting ===
            if item.current_demand:
                # 1. Convert to string
                # 2. Replace comma
                # 3. Replace ' MW'
                # 4. Strip whitespace (handles \xa0)
                cleaned_str = str(item.current_demand).replace(',', '').replace('MW', '').strip()
                if cleaned_str and cleaned_str != '-':
                    current_demand_data.append(int(cleaned_str))
                else:
                    current_demand_data.append(0)
            else:
                current_demand_data.append(0)

            if item.yesterday_demand:
                cleaned_str = str(item.yesterday_demand).replace(',', '').replace('MW', '').strip()
                if cleaned_str and cleaned_str != '-':
                    yesterday_demand_data.append(int(cleaned_str))
                else:
                    yesterday_demand_data.append(0)
            else:
                 yesterday_demand_data.append(0)

        except (ValueError, TypeError):
            # Fallback if cleaning still fails
            current_demand_data.append(0)
            yesterday_demand_data.append(0)

        if i > 0:
            previous_item = recent_data[i-1]
            time_diff = item.captured_at - previous_item.captured_at
            time_between_captures.append(round(time_diff.total_seconds(), 2))

    latest_data_point = recent_data_qs[0]

    data = {
        'latest_data_card': {
            'date': latest_data_point.date.strftime('%B %d, %Y'),
            'time_block': latest_data_point.time_block,
            'current_demand': latest_data_point.current_demand,
            'yesterday_demand': latest_data_point.yesterday_demand,
            'captured_at': latest_data_point.captured_at.strftime('%B %d, %Y, %I:%M %p'),
        },
        'chart_data': {
            'labels': labels,
            'current_demand': current_demand_data,
            'yesterday_demand': yesterday_demand_data,
            'capture_interval': time_between_captures,
        }
    }
    
    return JsonResponse(data)


def demand_data_list_api(request):
    """
    API endpoint for DemandData database records only.
    Defaults to today's records. Use ?date=YYYY-MM-DD for past records.
    """
    date_filter = request.GET.get('date')

    if date_filter:
        try:
            selected_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse(
                {'error': 'date must be in YYYY-MM-DD format'},
                status=400
            )
    else:
        selected_date = timezone.localdate()

    records = DemandData.objects.filter(date=selected_date).order_by('-captured_at')

    limit = request.GET.get('limit')
    if limit:
        try:
            limit = max(1, min(int(limit), 1000))
            records = records[:limit]
        except ValueError:
            return JsonResponse({'error': 'limit must be a number'}, status=400)

    return JsonResponse(
        [serialize_demand_data(item) for item in records],
        safe=False
    )


def demand_data_detail_api(request, pk):
    """
    API endpoint for one database demand record.
    """
    try:
        item = DemandData.objects.get(pk=pk)
    except DemandData.DoesNotExist:
        return JsonResponse({'error': 'Demand data not found'}, status=404)

    return JsonResponse(serialize_demand_data(item))
