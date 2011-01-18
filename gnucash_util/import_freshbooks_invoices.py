#!/usr/bin/env python

#
# Import an invoice from a freshbooks.com CSV export file.
#

# Usage:
#
# gnucash-env gnc-import-invoice GNUCASH CSV INV_ID

import csv
import datetime
import decimal
import os
import sys

from gnucash import Session, GncNumeric
from gnucash.gnucash_business import Customer, Invoice, Entry


def gnc_numeric_from_string(numeric_string):
    decimal_value = decimal.Decimal(numeric_string)
    sign, digits, exponent = decimal_value.as_tuple()

    # convert decimal digits to a fractional numerator
    # equivlent to
    # numerator = int(''.join(digits))
    # but without the wated conversion to string and back,
    # this is probably the same algorithm int() uses
    numerator = 0
    TEN = int(decimal.Decimal(0).radix()) # this is always 10
    numerator_place_value = 1
    # add each digit to the final value multiplied by the place value
    # from least significant to most sigificant
    for i in xrange(len(digits)-1,-1,-1):
        numerator += digits[i] * numerator_place_value
        numerator_place_value *= TEN

    if decimal_value.is_signed():
        numerator = -numerator

    # if the exponent is negative, we use it to set the denominator
    if exponent < 0 :
        denominator = TEN ** (-exponent)
    # if the exponent isn't negative, we bump up the numerator
    # and set the denominator to 1
    else:
        numerator *= TEN ** exponent
        denominator = 1

    return GncNumeric(numerator, denominator)

def import_invoice(import_invoice_number):
    reader = csv.reader(open(sys.argv[2], 'r'))
    header = reader.next()

    invoice = None
    for row in reader:

        import_client_name = row[0]
        client_id = client_ids[import_client_name]
        client = book.CustomerLookupByID(client_id)
        invoice_number = row[1]
        entry_description = row[5]
        unit_cost = row[7]
        quantity = row[8]
        line_cost = row[12]

        if import_invoice_number != invoice_number:
            continue

        if invoice is None:
            existing_invoice = book.InvoiceLookupByID(invoice_number)
            assert(existing_invoice is None), \
                'Invoice %s already exists' % (invoice_number, )

            assert(client != None)
            invoice = Invoice(book, invoice_number, USD, client)
            invoice_date = datetime.datetime.strptime(row[2], '%Y-%m-%d')
            invoice.SetDateOpened(invoice_date)

        invoice_entry = Entry(book, invoice)
        invoice_entry.SetDescription(entry_description)
        invoice_entry.SetQuantity(gnc_numeric_from_string(quantity))
        invoice_entry.SetInvAccount(consulting_income)
        invoice_entry.SetInvPrice(gnc_numeric_from_string(unit_cost))
        invoice_entry.SetDate(invoice_date)
        invoice_entry.SetDateEntered(invoice_date)

        if 'debug' in sys.argv:
            print '\n(ent) '.join(n for n in dir(invoice_entry) if n[0] != '_')
            print '\n(inv) '.join(n for n in dir(invoice) if n[0] != '_')
            sys.argv.remove('debug')

    invoice.PostToAccount(receivables, invoice_date,
                          invoice_date, "", True)
    invoice.SetDatePosted(invoice_date)


uri = "xml://%s" % os.path.abspath(sys.argv[1])

#
# File format is:
#
# Foo Inc.=1001
# Itty LLC=1002
# Bitty LP=1003
# Peta Corp.=1004
#
with open('%s/.gnc-import-clients' % (os.environ['HOME'], ), 'r') as f:
    client_ids = dict([line.strip().split('=') for line in f])

ses = Session(uri, is_new=False)
try:
    book = ses.get_book()
    commod_table = book.get_table()
    USD = commod_table.lookup('CURRENCY', 'USD')

    income = book.get_root_account().lookup_by_name("Income")
    consulting_income = income.lookup_by_name("Consulting")
    assert(income)
    assert(consulting_income)

    assets = book.get_root_account().lookup_by_name("Assets")
    receivables = book.get_root_account().lookup_by_name(
        "Accounts Receivable")
    assert(assets)
    assert(receivables)

    if '-' not in sys.argv[3]:
        import_invoice(sys.argv[3])
    else:
        # To import a range of invoices, provide the string format,
        # and low-high invoice numbers like:
        #
        # %04d-24-55
        #
        # This will import invoices 0024 through 0055 inclusive.
        #
        format, low, high = sys.argv[3].split('-')
        for invoice_id in range(int(low), int(high) + 1):
            import_invoice(format % invoice_id)

    if 'save' in sys.argv:
        print "saving..."
        ses.save()
finally:
    ses.end()
