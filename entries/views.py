import io
from django.http import FileResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from django.urls import reverse_lazy
from django.db.models import Sum
from django.db.models.functions import Greatest
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from .models import Entry
from .forms import EntryForm
from django.core.paginator import Paginator

class DashboardView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_entries = Entry.objects.all()
        
        # Calculate summary metrics (Balance removed)
        totals = all_entries.aggregate(
            total_money=Sum('money'),
            total_income=Sum('income')
        )
        total_money = totals['total_money'] or 0
        total_income = totals['total_income'] or 0
        
        context['total_money'] = total_money
        context['total_income'] = total_income
        context['total_records'] = all_entries.count()
        context['recent_entries'] = all_entries.annotate(max_amount=Greatest('money', 'income')).order_by('-max_amount')[:10]
        
        return context


def render_single_page_list(view_instance, form, is_editing=False, editing_entry=None, form_action=None):
    all_entries = Entry.objects.annotate(max_amount=Greatest('money', 'income')).order_by('-max_amount')
    
    # Calculate totals (Balance removed)
    totals = all_entries.aggregate(
        total_money=Sum('money'),
        total_income=Sum('income')
    )
    total_money = totals['total_money'] or 0
    total_income = totals['total_income'] or 0

    # Pagination
    paginator = Paginator(all_entries, 10)
    page_number = view_instance.request.GET.get('page') or 1
    page_obj = paginator.get_page(page_number)

    context = {
        'entries': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'paginator': paginator,
        'filtered_total_money': total_money,
        'filtered_total_income': total_income,
        'form': form,
        'is_editing': is_editing,
        'editing_entry': editing_entry,
        'form_action': form_action or reverse_lazy('entry_create'),
    }
    return render(view_instance.request, 'entry_list.html', context)


class EntryListView(View):
    def get(self, request, *args, **kwargs):
        edit_id = request.GET.get('edit')
        if edit_id:
            entry = get_object_or_404(Entry, pk=edit_id)
            form = EntryForm(instance=entry)
            form_action = reverse_lazy('entry_update', args=[entry.pk])
            return render_single_page_list(self, form, is_editing=True, editing_entry=entry, form_action=form_action)
        else:
            form = EntryForm()
            return render_single_page_list(self, form)


class EntryCreateView(SuccessMessageMixin, CreateView):
    model = Entry
    form_class = EntryForm
    success_url = reverse_lazy('entry_list')
    success_message = "Entry created successfully!"

    def get(self, request, *args, **kwargs):
        return redirect('entry_list')

    def form_invalid(self, form):
        return render_single_page_list(self, form)


class EntryUpdateView(SuccessMessageMixin, UpdateView):
    model = Entry
    form_class = EntryForm
    success_url = reverse_lazy('entry_list')
    success_message = "Entry updated successfully!"

    def get(self, request, *args, **kwargs):
        return redirect(f"{reverse_lazy('entry_list')}?edit={self.kwargs['pk']}")

    def form_invalid(self, form):
        form_action = reverse_lazy('entry_update', args=[self.object.pk])
        return render_single_page_list(self, form, is_editing=True, editing_entry=self.object, form_action=form_action)


class EntryDeleteView(SuccessMessageMixin, DeleteView):
    model = Entry
    success_url = reverse_lazy('entry_list')
    success_message = "Entry deleted successfully!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class ExportPDFView(View):
    def get(self, request, *args, **kwargs):
        school_name = request.GET.get('school_name') or 'School Name'
        budget_period = request.GET.get('budget_period') or 'Budget 2025 July to 2026 June'

        # Order entries by the largest amount descending
        entries = Entry.objects.annotate(max_amount=Greatest('money', 'income')).order_by('-max_amount')

        totals = entries.aggregate(
            total_money=Sum('money'),
            total_income=Sum('income')
        )
        total_money = totals['total_money'] or 0
        total_income = totals['total_income'] or 0

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=40, 
            leftMargin=40, 
            topMargin=40, 
            bottomMargin=40
        )
        
        elements = []
        styles = getSampleStyleSheet()

        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#1e293b')
        )
        cell_header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.white
        )
        
        # Premium Header Table
        header_left = f"<font size='22'><b>{school_name}</b></font><br/><font size='10' color='#71717a'>{budget_period}</font>"
        header_right = f"<font size='10'><b>BUDGET REPORT</b></font><br/><font size='9' color='#a1a1aa'>Generated: {timezone.now().strftime('%d-%m-%Y')}</font>"
        
        header_data = [
            [
                Paragraph(header_left, styles['Normal']), 
                Paragraph(header_right, ParagraphStyle('RightHeader', parent=styles['Normal'], alignment=2))
            ]
        ]
        
        header_table = Table(header_data, colWidths=[360, 160])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#e4e4e7')),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 20))

        # Main Data Table
        table_data = [
            [
                Paragraph("Name", cell_header_style), 
                Paragraph("Expense", cell_header_style), 
                Paragraph("Income", cell_header_style), 
                Paragraph("Date", cell_header_style)
            ]
        ]

        for entry in entries:
            money_val = f"Rs. {entry.money:,.2f}" if entry.money > 0 else "-"
            income_val = f"Rs. {entry.income:,.2f}" if entry.income > 0 else "-"
            date_val = entry.date.strftime('%d-%m-%Y') if entry.date else "-"
            
            table_data.append([
                Paragraph(entry.name, cell_style),
                Paragraph(money_val, cell_style),
                Paragraph(income_val, cell_style),
                Paragraph(date_val, cell_style)
            ])

        col_widths = [240, 100, 100, 80]
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181b')), # Dark zinc header
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f9f9fb')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e4e4e7')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))

        # Bottom Totals Summary Table (Balance removed)
        summary_cell_header_style = ParagraphStyle(
            'SummaryHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#4b5563')
        )
        summary_cell_value_style = ParagraphStyle(
            'SummaryValue',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#09090b')
        )
        summary_money_style = ParagraphStyle(
            'SummaryMoney',
            parent=summary_cell_value_style,
            textColor=colors.HexColor('#dc2626') # Red-600
        )
        summary_income_style = ParagraphStyle(
            'SummaryIncome',
            parent=summary_cell_value_style,
            textColor=colors.HexColor('#059669') # Emerald-600
        )

        summary_data = [
            [
                Paragraph("Total Expense", summary_cell_header_style),
                Paragraph("Total Income", summary_cell_header_style)
            ],
            [
                Paragraph(f"Rs. {total_money:,.2f}", summary_money_style),
                Paragraph(f"Rs. {total_income:,.2f}", summary_income_style)
            ]
        ]
        
        st = Table(summary_data, colWidths=[260, 260])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f4f5')), # Light zinc
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e4e4e7')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(st)

        doc.build(elements)
        buffer.seek(0)
        
        return FileResponse(buffer, as_attachment=False, filename='budget_entries.pdf')
