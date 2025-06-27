from celery import shared_task
from datetime import datetime
from .models import Payment
from django.utils import timezone
import calendar


@shared_task
def pay_salary():
    
    today = timezone.now()
    today_weekday=today.weekday()

    days_in_month = calendar.monthrange(today.year, today.month)[1]

    if today.day == days_in_month:
        # If today is the last day of the month and payment date is bigger then today
        payments = Payment.objects.filter(next_salary_date__gte=str(today.day))    
    else:
        # Find all payments where frequency matches today_day
        payments = Payment.objects.filter(next_salary_date=str(today.day))


    for emp in payments:
        # day_in_last_month=calendar.monthrange(emp.last_salary_date.year, emp.last_salary_date.month)[1]
        total_days=(today-emp.last_salary_date).days
        last_weekday=emp.last_salary_date.weekday()

        total_weekend_days=0
        # print(f"----------------------------------")
        # print(last_weekday, " day: ", today_weekday)
        # print(f"----------------------------------")
        # print(f"----------------------------------")
        # print(total_days, " date: ", today)
        # print(f"----------------------------------")

        # This logic is for only calculating the weekend_days
        if last_weekday > today_weekday:
            if last_weekday == 6 :
                total_weekend_days=-1
            total_days=total_days+(last_weekday-today_weekday)
        elif today_weekday > last_weekday :
            if today_weekday == 6:
                total_weekend_days=-1
            else:
                total_weekend_days=-2
            total_days=total_days+(7-(today_weekday-last_weekday))


        total_weekend_days=total_weekend_days+((total_days//7)*2)
        
        # Actual total days
        # print(f"----------------------------------")
        # print(total_days)
        # print(f"----------------------------------")
        total_days=(today-emp.last_salary_date).days
        total_days=total_days-total_weekend_days
        # print(f"----------------------------------")
        # print(total_days)
        # print(f"----------------------------------")


        if total_days > 0:
            # Here i am calculating the salary based on 8 hours of work day
            emp.last_salary_amount=total_days*8*emp.salary_per_hour
            emp.last_salary_date=timezone.now()

            if emp.payment_cycle == 'Weekly':
                emp.next_salary_date=str((today.day+7)%days_in_month)
            elif emp.payment_cycle == 'Bi-weekly':
                emp.next_salary_date=str((today.day+14)%days_in_month)
            elif emp.payment_cycle == 'Twice in month':
                emp.next_salary_date, emp.payment_frequency = emp.payment_frequency, emp.next_salary_date
            emp.save()   
            print(f"----------------------------------")
            print(f"Updated payment record for {emp.employee.user.email} | Last Salary Date: {emp.last_salary_date} | Last Salary Amt: {emp.last_salary_amount}")
            print(f"----------------------------------")
        
            
            


        # if today_weekday==6:
        #     total_weekend_days=-1
        # else:
        #     total_weekend_days=-2
        # total_days=total_days+(7-today_weekday)

        # if last_weekday==6:
        #     total_weekend_days=total_weekend_days-1
        #     total_days=total_days-(7-last_weekday)
        # else:
        #     total_weekend_days=total_weekend_days+2
        #     total_days=total_days-(7-last_weekday)

        # # total_days=total_days+1

        # total_weekend_days=total_weekend_days+(((total_days+1)/7)*2)
        # # total_weekend_days=total_weekend_days*2

        # total_days=(int(today.day)-int(emp.last_salary_date.day))%day_in_last_month
        # total_days=total_days-total_weekend_days

        # emp.last_salary_amount=total_days*8*emp.salary_per_hour
        # emp.last_salary_date=timezone.now()
        # emp.save()

