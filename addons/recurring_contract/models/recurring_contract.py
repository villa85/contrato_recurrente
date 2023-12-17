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
    product_id = fields.Many2one('product.product', string='Product', required=True)
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
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain="[('type', '=', 'sale'), ('company_id', '=', company_id)]")
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')
    date_start = fields.Date(string='Start Date', default=fields.Date.today(), help='To Add subscription contract start date')
    date_end = fields.Date(string='End Date', help='Subscription End Date')
    state = fields.Selection([
        ('New', 'New'),
        ('Ongoing', 'Ongoing'),
        ('Expire Soon', 'Expire Soon'),
        ('Expired', 'Expired'),
        ('Cancelled', 'Cancelled'),
    ], string='Stage', default='New', copy=False, tracking=True,
        readonly=True, help='Status of subscription contract')
    lock = fields.Boolean(string='Lock', default=False,
                        help='To lock subscription contract')

    def action_to_confirm(self):
        """ Button to confirm """
        self.write({'state': 'Ongoing'})

    def action_lock(self):
        """ Button to lock subscription contract """
        self.lock = True

    def action_generate_invoice(self):
        """ Button to generate invoice """
        self.ensure_one()
        invoice_vals = self._prepare_invoice_vals()
        # invoice_vals.update({'invoice_line_ids': [(0, 0, self._prepare_invoice_line_vals())]})
        invoice = self.env['account.move'].create(invoice_vals)
        return self.action_view_invoice(invoice)

    def _prepare_invoice_vals(self):
        vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'fiscal_position_id': self.partner_id.property_account_position_id and self.partner_id.property_account_position_id.id or False,
            'company_id': self.company_id.id,
            'invoice_date': fields.date.today(),
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'invoice_payment_term_id': self.invoice_payment_term_id.id if self.invoice_payment_term_id else False,
            'invoice_line_ids': [] #,
            # 'narration': self.notes
        }
        return vals

    def _prepare_invoice_line_vals(self):
        vals = {
            'product_id': self.product_id.id, # estoy por aca
            'quantity': self.quantity,
            'display_type': 'product',
            'price_unit': self.price_unit,
            'analytic_distribution': {str(self.analytic_account_id.id): 100} if self.analytic_account_id else False,
            'name': self.product_id.name,
        }
        return vals


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

    @api.depends('budget_id.produc_id')
    def _compute_product_budget(self):
        if self.budget_id:
            # Actualiza el campo produc_id con el valor del presupuesto seleccionado
            self.produc_id = self.budget_id.produc_id.id