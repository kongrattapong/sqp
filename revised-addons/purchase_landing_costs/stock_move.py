# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 OpenERP s.a. (<http://www.openerp.com>).
#    Copyright (C) 2012 Mentis d.o.o. (<http://www.mentis.si>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

#----------------------------------------------------------
#  Stock Move INHERIT
#----------------------------------------------------------
class stock_move(osv.osv):
    _inherit = "stock.move"   

    # per amount landing costs amount
    def _landing_costs_per_value(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}        
        result = {}
        for line in self.browse(cr, uid, ids):
            per_value = 0.0
            if line.landing_costs_line_ids:
                for costs in line.landing_costs_line_ids:
                    if costs.distribution_type == 'per_value':
                        per_value += costs.amount
            result[line.id] = per_value
        return result

    # per unit landing costs amount
    def _landing_costs_per_unit(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}        
        result = {}
        for line in self.browse(cr, uid, ids):
            per_unit = 0.0
            if line.landing_costs_line_ids:
                for costs in line.landing_costs_line_ids:
                    if costs.distribution_type == 'per_unit':
                        per_unit += costs.amount
            result[line.id] = per_unit
        return result

    # stock move quantity for cost calculation
    def _landing_costs_base_quantity(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}
        result = {}
        base_quantity = 0.0
        for line in self.browse(cr, uid, ids):
            if line.product_id.landing_cost_calculate:
                base_quantity = line.product_qty
            result[line.id] = base_quantity
        return result
    
    # stock move amount for costs calculation
    def _landing_costs_base_amount(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}
        result = {}
        base_amount = 0.0
        for line in self.browse(cr, uid, ids):
            if line.product_id.landing_cost_calculate:
                base_amount = line.price_unit * line.product_qty
            result[line.id] = base_amount
        return result

    def _landing_costs_price_unit_with_costs(self, cr, uid, ids, name, args, context):
        if not ids:
            return {}
        result = {}

        for line in self.browse(cr, uid, ids):
            price_unit_with_costs = line.price_unit_without_costs
            if line.product_id.landing_cost_calculate:
                if line.picking_id and (line.picking_id.landing_costs_per_value > 0.0 or line.picking_id.landing_costs_per_unit > 0.0):       
                    # landing costs - picking - amount
                    if line.picking_id.landing_costs_base_amount > 0.0 and line.product_qty > 0.0:
                        price_unit_with_costs += ((line.picking_id.landing_costs_per_value / line.picking_id.landing_costs_base_amount) * (line.price_unit * line.product_qty)) / line.product_qty
                    # landing costs - picking - quantity
                    if line.product_qty > 0.0:
                        price_unit_with_costs += line.picking_id.landing_costs_per_unit / line.picking_id.landing_costs_base_quantity
                                    
                # landing costs - move
                if line.product_qty > 0.0 and (line.landing_costs_per_value > 0.0 or line.landing_costs_per_unit > 0.0):
                    price_unit_with_costs += (line.landing_costs_per_value + line.landing_costs_per_unit) / line.product_qty                                     

            if line.price_unit != price_unit_with_costs:
                self.write(cr, uid, [line.id], {'price_unit': price_unit_with_costs})                 
            result[line.id] = price_unit_with_costs
            
        return result

    _columns = { 
          'price_unit_without_costs': fields.float('', digits_compute=dp.get_precision('Account'), ),
          'price_unit_with_costs': fields.function(_landing_costs_price_unit_with_costs, digits_compute=dp.get_precision('Amount'), ),
          'landing_costs_line_ids': fields.one2many('purchase.landing.cost.position', 'move_line_id', 'Landing Costs'),
          'landing_costs_per_value': fields.function(_landing_costs_per_value, digits_compute=dp.get_precision('Account'), string='Landing Costs Amount Per Value For Average Price'),
          'landing_costs_per_unit': fields.function(_landing_costs_per_unit, digits_compute=dp.get_precision('Account'), string='Landing Costs Amount Per Unit For Average Price'),
          'landing_costs_base_quantity': fields.function(_landing_costs_base_quantity, digits_compute=dp.get_precision('Account'), string='Stock Move Quantity For Per Unit Calculation'),
          'landing_costs_base_amount': fields.function(_landing_costs_base_amount, digits_compute=dp.get_precision('Account'), string='Stock Move For Per Value Calculation'),
    }
    
stock_move()
