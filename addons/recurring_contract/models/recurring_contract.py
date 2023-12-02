# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
""" Recurring contract """
# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import date_utils
from odoo.tools.safe_eval import datetime

class RecurringContract(models.Model):
    _name = "recurring.contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Contract Name', required=True, help='To add contract name')
    budget_id = fields.Many2one('sale.order',string='Budget', help='To add budget reference')
    amount_total_budget = fields.Monetary(string='Amount Total', store=True, compute='_compute_amount_total_budget', readonly=True, help='Show Total Amount')
    contacts = fields.Many2many('res.partner',  string='Contacts', help='To add contracts reference')
    partner_id = fields.Many2one('res.partner', string="Customer",help='To add Customer')
    recurring_period = fields.Integer(string='Recurring Period', help='To add recurring period of subscription contract')
    recurring_period_interval = fields.Selection([
        ('Days', 'Days'),
        ('Weeks', 'Weeks'),
        ('Months', 'Months'),
        ('Years', 'Years'),
    ], help='To add recurring interval of subscription contract')
    contract_reminder = fields.Integer(string='Contract Expiration Reminder (Days)', help='Add expiry reminder of subscription contract in days.')
    recurring_invoice = fields.Integer(string='Recurring Invoice Interval (Days)', help='Add recurring invoice interval in days')
    next_invoice_date = fields.Date(string='Next Invoice Date', store=True,compute='_compute_next_invoice_date', help='Add date of next invoice')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, help='To get company')
    currency_id = fields.Many2one('res.currency', string='Currency', help='To get currency', required=True, default=lambda self: self.env.company.currency_id)
    date_start = fields.Date(string='Start Date', default=fields.Date.today(), help='To Add subscription contract start date')
    date_end = fields.Date(string='End Date', help='Subscription End Date')


    @api.depends('date_start', 'recurring_invoice', 'recurring_period',
                'recurring_period_interval')
    def _compute_next_invoice_date(self):
        """ Compute next invoice date """
        self.next_invoice_date = fields.Date.today()
        start_date = self.date_start
        interval = self.recurring_invoice
        recurring_period = self.recurring_period
        recurring_period_interval = self.recurring_period_interval
        self.next_invoice_date = date_utils.add(start_date,
                                                days=int(interval))
        if recurring_period_interval == 'Days':
            next_schedule = date_utils.add(start_date,
                                        days=int(recurring_period))
            self.date_end = next_schedule
        elif recurring_period_interval == 'Weeks':
            next_schedule = date_utils.add(start_date,
                                        weeks=int(recurring_period))
            self.date_end = next_schedule
        elif recurring_period_interval == 'Months':
            next_schedule = date_utils.add(start_date,
                                        months=int(recurring_period))
            self.date_end = next_schedule
        else:
            next_schedule = date_utils.add(start_date,
                                        years=int(recurring_period))
            self.date_end = next_schedule

    @api.depends('budget_id.amount_total')
    def _compute_amount_total_budget(self):
        for record in self:
            record.amount_total_budget = record.budget_id.amount_total if record.budget_id else 0.0