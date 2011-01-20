#!/usr/bin/env python

#
# Generate a PDF from a GnuCash invoice.
#

# Usage:
#
# gnucash-env python -m gnucash_util.invoice_pdf \
#     GNUCASH_FILE INVOICE_NUMBER PDF_FILE

import csv
import datetime
import decimal
import os
import sys

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm, mm, inch, pica

from gnucash import Session, GncNumeric
from gnucash.gnucash_business import Customer, Invoice, Entry


def invoice_pdf(gnc_file, invoice_number, pdf_file):
    uri = "xml://{0}".format(os.path.abspath(gnc_file))
    ses = Session(uri, is_new=False)
    try:
        book = ses.get_book()
        commod_table = book.get_table()
        USD = commod_table.lookup('CURRENCY', 'USD')

        invoice = book.InvoiceLookupByID(invoice_number)
        client = invoice.GetOwner()
        client_addr = client.GetAddr()

        pdf = Canvas(pdf_file, bottomup=False, pagesize=letter)

        pdf.setFont("Helvetica-Bold", 24)
        pdf.setFillColor(colors.lightgrey)
        pdf.drawCentredString(letter[0] / 2, inch * 0.75, "INVOICE")

        font_height = 10
        pdf.setFont("Helvetica", font_height)
        pdf.setFillColor(colors.black)
        from_header = pdf.beginText(inch * 0.75, inch * 0.75)
        to_header = pdf.beginText(inch * 0.75, inch * 2.25)

        header_file = '{0}/.gnc-invoice-header'.format(os.environ['HOME'])
        with open(header_file, 'r') as f:
            for line in f:
                from_header.textLine(line.strip())

        to_fields = [
            client.GetName(),
            client_addr.GetName(),
            client_addr.GetAddr1(),
            client_addr.GetAddr2(),
            client_addr.GetAddr3(),
            client_addr.GetAddr4(),
            ]
        for field in to_fields:
            if field:
                to_header.textLine(field)

        pdf.drawText(from_header)
        pdf.drawText(to_header)

        #
        # This is the summary table / box in the mid-upper right.
        #
        table_data = (("Invoice #",
                       invoice.GetID()),
                      ("Date",
                       invoice.GetDatePosted().strftime("%Y-%m-%d")),
                      ("Amount Due (USD)",
                       '${0:0.2f}'.format(invoice.GetTotal().to_double())))
        x = inch * 4.5
        y = (inch * 2.25) - font_height
        width = (inch * 3)
        height = (inch * 0.75)
        num_rows = 3
        num_cols = 2
        col_width = width / num_cols
        row_height = height / num_rows
        for row in range(num_rows):
            for col in range(num_cols):
                rect_x = x + (col_width * col)
                rect_y = y + (row_height * row)

                pdf.setFillColor(colors.darkgrey)
                pdf.rect(rect_x,
                         rect_y,
                         col_width,
                         row_height,
                         stroke=True,
                         fill=(col == 0))
                
                pdf.setFillColor(colors.black)
                if col:
                    pdf.drawAlignedString(rect_x + col_width,
                                          rect_y + font_height + 2,
                                          table_data[row][col],
                                          '%')
                else:
                    pdf.drawString(rect_x + 5,
                                   rect_y + font_height + 2,
                                   table_data[row][col])

        #
        # This is the detail table in the lower half.
        #
        table_data = [
            ("Date", "Description", "Hours", "Rate ($)", "Line Total"),
            ]
        for entry in [Entry(instance=e) for e in
                      invoice.GetEntries()]:
            qty = GncNumeric(instance=entry.GetQuantity()).to_double()
            rate = GncNumeric(instance=entry.GetInvPrice()).to_double()
            line_total = GncNumeric(instance=entry.ReturnValue(True)).to_double()
            row = [entry.GetDate().strftime("%Y-%m-%d"),
                   entry.GetDescription(),
                   '{0:0.2f}'.format(qty),
                   '{0:0.2f}'.format(rate),
                   '{0:0.2f}'.format(line_total),
                   ]
            table_data.append(row)


        x = inch * 0.75
        y = (inch * 4.0)

        # Let column 1 consume the rest of the space.
        width = (inch * 6.75)
        widths = [80, 0, 50, 50, 80]
        widths[1] = width - sum(widths)

        height = (font_height + 2 + 2)  # 2pt spacing above and below.
        num_rows = 1
        num_cols = 5
        col_width = width / num_cols
        row_height = height / num_rows
        rect_x = x
        rect_y = y
        for row_num, row in enumerate(table_data):
            rect_x = x
            for col_num, col in enumerate(row):
                col_width = widths[col_num]
                rect_y = y + (row_height * row_num)

                pdf.setFillColor(colors.darkgrey)
                pdf.rect(rect_x,
                         rect_y,
                         col_width,
                         row_height,
                         stroke=True,
                         fill=(row_num == 0))
                
                pdf.setFillColor(colors.black)
                if col_num > 1:
                    pdf.drawAlignedString(rect_x + col_width,
                                          rect_y + font_height + 2,
                                          col,
                                          '%')
                else:
                    pdf.drawString(rect_x + 5,
                                   rect_y + font_height + 2,
                                   col)

                rect_x = rect_x + col_width
        
        # Draw the outer detail box.
        detail_height = inch * 5.0
        pdf.setFillColor(colors.black)
        pdf.rect(x,
                 y,
                 width,
                 detail_height,
                 stroke=True,
                 fill=False)

        # Total box above payment terms.
        totalbox_text_vpad = 6
        totalbox_text_height = font_height + (totalbox_text_vpad * 2)
        totalbox_rows = 4
        totalbox_height = totalbox_text_height * (totalbox_rows + 1)
        totalbox_y = y + detail_height - totalbox_height
        pdf.rect(x,
                 totalbox_y,
                 width,
                 totalbox_height,
                 stroke=True,
                 fill=False)

        # Total, balance due, etc boxes inside total box.
        total_amount = invoice.GetTotal().to_double()
        totalbox_data = [
            ('Subtotal:', '${0:0.2f}'.format(total_amount)),
            ('Total:', '${0:0.2f}'.format(total_amount)),
            ('Amount Paid:', '$0.00'),
            ('Balance Due:', '${0:0.2f}'.format(total_amount)),
            ]
        balance_height = row_height
        balance_y = (totalbox_y +
                     totalbox_height -
                     totalbox_text_height * 2)
        for n in xrange(totalbox_rows):
            thisbox_y = totalbox_y + totalbox_text_height * n
            thisbox_text_y = (thisbox_y + totalbox_text_height -
                              totalbox_text_vpad)
            pdf.setFillColor(colors.lightgrey)
            pdf.rect(x + width / 2,
                     thisbox_y,
                     width / 2,
                     totalbox_text_height,
                     stroke=True,
                     fill=(n == (totalbox_rows - 1)))
            pdf.setFillColor(colors.black)
            pdf.drawAlignedString(x + width / 2 + (inch * 1.5),
                                  thisbox_text_y,
                                  totalbox_data[n][0],
                                  ':')
            pdf.drawAlignedString(x + width - 20,
                                  thisbox_text_y,
                                  totalbox_data[n][1],
                                  '.')

        # Payment terms in the bottom of the detail box.
        pdf.setFillColor(colors.black)
        pdf.rect(x,
                 y + detail_height - totalbox_text_height,
                 width,
                 totalbox_text_height,
                 stroke=True,
                 fill=False)

        if invoice.GetTerms() and invoice.GetTerms().GetDueDays():
            due = 'Payment due within %d days of invoice date.' % (
                invoice.GetTerms().GetDueDays())
            pdf.setFillColor(colors.black)
            pdf.drawCentredString(
                x + (width / 2),
                y + detail_height - totalbox_text_vpad,
                due)

        pdf.showPage()
        pdf.save()
    finally:
        ses.end()


if __name__ == '__main__':
    invoice_pdf(sys.argv[1], sys.argv[2], sys.argv[3])
