# financial_calculator/gui/acc_input_gui.py

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any, List

from .base_gui import BaseGUI
from utils.validation import (
    validate_numeric_input, validate_positive_numeric_input,
    validate_non_negative_numeric_input, validate_percentage_input,
    validate_list_input, validate_numeric_range,
    validate_positive_integer_input, validate_non_negative_integer_input
)
import config

from mathematical_functions.accounting_basics import (
    PnL, BalanceSheet, CashFlowStatement, FinancialStatements,
    BaseYearData, Assumptions, generate_basic_financials
)
from mathematical_functions.accounting_advanced import (
    AdvancedAssumptions, generate_advanced_financials
)
from mathematical_functions.accounting_ratios import calculate_ratios_for_year, calculate_all_ratios

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class AccountingInputGUI(BaseGUI):
    def __init__(self, parent, controller=None, *args, **kwargs):
        super().__init__(parent, controller, *args, **kwargs)
        self.name = "AccountingInputGUI"
        self.configure(style="InputGUI.TFrame")

        self.input_sections: Dict[str, ttk.LabelFrame] = {}
        self.advanced_mode_var = tk.BooleanVar(value=False)
        self.advanced_mode_var.trace_add("write", self._toggle_input_sections_visibility)

        self._create_input_widgets(self.scrollable_frame)
        self._toggle_input_sections_visibility()

        self.calculate_button.config(text="Generate Financial Statements", command=self.calculate_financial_statements)
        logger.info("AccountingInputGUI initialized.")

    def _create_input_widgets(self, parent_frame):
        title_label = ttk.Label(parent_frame, text="Financial Model Inputs (P&L, BS, CFS)",
                                 style="Title.TLabel")
        title_label.grid(row=0, column=0, columnspan=2, pady=(10, 20), sticky="ew")

        advanced_toggle = ttk.Checkbutton(parent_frame,
                                          text="Enable Advanced Input Mode",
                                          variable=self.advanced_mode_var,
                                          style="Toggle.TCheckbutton")
        advanced_toggle.grid(row=1, column=0, columnspan=2, pady=(0, 10), padx=10, sticky="w")

        current_row = 2

        # Base Year Section
        base_data_frame = ttk.LabelFrame(parent_frame, text="Base Year (Year 0) Data", style="InputSection.TLabelframe")
        base_data_frame.grid(row=current_row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.input_sections['base_data'] = base_data_frame
        self._populate_base_data_inputs(base_data_frame)
        current_row += 1

        # Core Assumptions
        core_assumptions_frame = ttk.LabelFrame(parent_frame, text="Core Assumptions", style="InputSection.TLabelframe")
        core_assumptions_frame.grid(row=current_row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.input_sections['core_assumptions'] = core_assumptions_frame
        self._populate_core_assumptions_inputs(core_assumptions_frame)
        current_row += 1

        # Advanced Assumptions (toggle)
        advanced_assumptions_frame = ttk.LabelFrame(parent_frame, text="Advanced Assumptions", style="InputSection.TLabelframe")
        self.input_sections['advanced_assumptions'] = advanced_assumptions_frame
        self._populate_advanced_assumptions_inputs(advanced_assumptions_frame)
        self.advanced_assumptions_row = current_row
        current_row += 1

        self.result_frame.grid(row=99, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.common_buttons_frame.grid(row=100, column=0, columnspan=2, pady=5)
        
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(1, weight=1)

    def _populate_base_data_inputs(self, parent_frame):
        row_idx = 0
        fields = [
            ("Revenue ($):", "1000000", 'base_revenue'),
            ("Cost of Goods Sold ($):", "600000", 'base_cogs'),
            ("Operating Expenses ($):", "200000", 'base_opex'),
            ("Depreciation (P&L) ($):", "50000", 'base_depreciation'),
            ("Interest Expense (P&L) ($):", "10000", 'base_interest_expense'),
            ("Cash ($):", "50000", 'base_cash'),
            ("Accounts Receivable ($):", "80000", 'base_ar'),
            ("Inventory ($):", "70000", 'base_inventory'),
            ("Gross Property, Plant & Equipment ($):", "400000", 'base_fixed_assets'),
            ("Accumulated Depreciation ($):", "100000", 'base_accumulated_depreciation'),
            ("Accounts Payable ($):", "50000", 'base_ap'),
            ("Long-Term Debt ($):", "200000", 'base_ltd'),
            ("Retained Earnings ($):", "700000", 'base_retained_earnings'),
        ]
        for label, default, key in fields:
            self.create_input_row(parent_frame, row_idx, label, default, "", key)
            row_idx += 1

    def _populate_core_assumptions_inputs(self, parent_frame):
        row_idx = 0
        fields = [
            ("Number of Forecast Years:", "5", 'num_forecast_years'),
            ("Revenue Growth Rates (%, comma-separated):", "10,8,6,4,3", 'revenue_growth_rates_str'),
            ("COGS as % of Revenue (%, comma-separated):", "60,58,56,55,55", 'cogs_as_pct_revenue_rates_str'),
            ("Operating Expenses as % of Revenue (%, comma-separated):", "20,19,18,17,17", 'opex_as_pct_revenue_rates_str'),
            ("Tax Rate (%):", "21", 'tax_rate_pct'),
            ("Interest Rate on Debt (%):", "5.0", 'interest_rate_pct'),
        ]
        for label, default, key in fields:
            self.create_input_row(parent_frame, row_idx, label, default, "", key)
            row_idx += 1

    def _populate_advanced_assumptions_inputs(self, parent_frame):
        row_idx = 0
        fields = [
            ("Accounts Receivable Days:", "30", 'ar_days'),
            ("Inventory Days:", "45", 'inventory_days'),
            ("Accounts Payable Days:", "40", 'ap_days'),
            ("Capital Expenditures as % of Revenue (%):", "2.0", 'capex_as_pct_revenue_pct'),
            ("Depreciation Rate (% of Gross PP&E):", "10", 'depreciation_rate_pct'),
            ("Dividend Payout Ratio (%):", "30", 'dividend_payout_ratio_pct'),
            ("Target Minimum Cash ($):", "50000", 'target_min_cash'),
            ("Interest Income on Cash Rate (%):", "1.0", 'interest_income_on_cash_rate_pct'),
            ("New Equity Issued ($):", "0.0", 'new_equity_issued'),
            ("Share Buybacks ($):", "0.0", 'share_buybacks'),
        ]
        for label, default, key in fields:
            self.create_input_row(parent_frame, row_idx, label, default, "", key)
            row_idx += 1

    def _toggle_input_sections_visibility(self, *args):
        is_advanced = self.advanced_mode_var.get()
        advanced_frame = self.input_sections['advanced_assumptions']
        if is_advanced:
            advanced_frame.grid(row=self.advanced_assumptions_row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
            logger.info("Advanced input mode enabled.")
        else:
            advanced_frame.grid_remove()
            logger.info("Advanced input mode disabled.")
        self.scrollable_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def calculate_financial_statements(self):
        """
        Gathers, validates, and processes all user inputs, then calls the
        financial model backend and displays the results.
        """
        self.display_result("Validating inputs and generating financial statements...", is_error=False)
        
        inputs: Dict[str, Any] = {}
        errors: List[str] = []

        # Helper to simplify validation and error accumulation
        def _validate_and_store(key: str, value_str: str, validation_type: str, field_name: str, 
                                 is_percentage: bool = False, is_list: bool = False, 
                                 list_item_type: str = 'numeric', min_val=None, max_val=None):
            is_valid = False
            processed_value = None
            
            if is_list:
                is_valid, temp_value = validate_list_input(value_str, list_item_type, field_name)
                if is_valid:
                    if is_percentage and list_item_type == 'numeric':
                        processed_value = [v / 100.0 for v in temp_value]
                    else:
                        processed_value = temp_value
                else:
                    errors.append(temp_value) # temp_value is the error message here
            else:
                if validation_type == 'numeric':
                    is_valid, temp_value = validate_numeric_input(value_str, field_name)
                elif validation_type == 'positive_numeric':
                    is_valid, temp_value = validate_positive_numeric_input(value_str, field_name)
                elif validation_type == 'non_negative_numeric':
                    is_valid, temp_value = validate_non_negative_numeric_input(value_str, field_name)
                elif validation_type == 'percentage': # This simply checks if it's a number. Conversion to 0-1 done below.
                    is_valid, temp_value = validate_percentage_input(value_str, field_name)
                elif validation_type == 'numeric_range':
                    is_valid, temp_value = validate_numeric_range(value_str, min_val, max_val, field_name)
                elif validation_type == 'positive_integer':
                    is_valid, temp_value = validate_positive_integer_input(value_str, field_name)
                elif validation_type == 'non_negative_integer':
                    is_valid, temp_value = validate_non_negative_integer_input(value_str, field_name)
                else:
                    logger.error(f"Unsupported validation type '{validation_type}' for field '{field_name}'.")
                    errors.append(f"Internal error: Invalid validation setup for {field_name}.")
                    return

                if is_valid:
                    if is_percentage:
                        processed_value = temp_value / 100.0
                    else:
                        processed_value = temp_value
                else:
                    errors.append(temp_value) # temp_value is the error message here

            if is_valid:
                inputs[key] = processed_value
            

        # --- Base Year Data Validation & Collection ---
        _validate_and_store('base_revenue', self.get_input_value('base_revenue'), 'positive_numeric', "Base Year Revenue")
        _validate_and_store('base_cogs', self.get_input_value('base_cogs'), 'non_negative_numeric', "Base Year COGS")
        _validate_and_store('base_opex', self.get_input_value('base_opex'), 'non_negative_numeric', "Base Year Operating Expenses")
        # ADDED Base Year P&L components
        _validate_and_store('base_depreciation', self.get_input_value('base_depreciation'), 'non_negative_numeric', "Base Year Depreciation")
        _validate_and_store('base_interest_expense', self.get_input_value('base_interest_expense'), 'non_negative_numeric', "Base Year Interest Expense")

        _validate_and_store('base_cash', self.get_input_value('base_cash'), 'non_negative_numeric', "Base Year Cash")
        _validate_and_store('base_ar', self.get_input_value('base_ar'), 'non_negative_numeric', "Base Year Accounts Receivable")
        _validate_and_store('base_inventory', self.get_input_value('base_inventory'), 'non_negative_numeric', "Base Year Inventory")
        _validate_and_store('base_fixed_assets', self.get_input_value('base_fixed_assets'), 'non_negative_numeric', "Base Year Fixed Assets")
        # ADDED Base Year Balance Sheet components
        _validate_and_store('base_accumulated_depreciation', self.get_input_value('base_accumulated_depreciation'), 'non_negative_numeric', "Base Year Accumulated Depreciation")

        _validate_and_store('base_ap', self.get_input_value('base_ap'), 'non_negative_numeric', "Base Year Accounts Payable")
        _validate_and_store('base_ltd', self.get_input_value('base_ltd'), 'non_negative_numeric', "Base Year Long-Term Debt")
        # ADDED Base Year Equity components
        _validate_and_store('base_retained_earnings', self.get_input_value('base_retained_earnings'), 'non_negative_numeric', "Base Year Equity") # Note: This is now Retained Earnings from the GUI, but named 'base_retained_earnings' in inputs for consistency with older code if you didn't rename it.


        # --- Core Assumptions Validation & Collection ---
        _validate_and_store('num_forecast_years', self.get_input_value('num_forecast_years'), 'positive_integer', "Number of Forecast Years")
        _validate_and_store('revenue_growth_rates', self.get_input_value('revenue_growth_rates_str'), 'numeric', "Revenue Growth Rates", is_percentage=True, is_list=True)
        _validate_and_store('cogs_as_pct_revenue_rates', self.get_input_value('cogs_as_pct_revenue_rates_str'), 'numeric', "COGS as % of Revenue", is_percentage=True, is_list=True)
        _validate_and_store('opex_as_pct_revenue_rates', self.get_input_value('opex_as_pct_revenue_rates_str'), 'numeric', "Operating Expenses as % of Revenue", is_percentage=True, is_list=True)
        
        _validate_and_store('tax_rate', self.get_input_value('tax_rate_pct'), 'numeric_range', "Tax Rate", is_percentage=True, min_val=0, max_val=100)
        _validate_and_store('interest_rate', self.get_input_value('interest_rate_pct'), 'non_negative_numeric', "Interest Rate on Debt", is_percentage=True)


        # --- Advanced Assumptions Validation & Collection (only if advanced mode is enabled) ---
        if self.advanced_mode_var.get():
            # Corrected to CamelCase to match AdvancedAssumptions dataclass field names
            _validate_and_store('AR_Days', self.get_input_value('ar_days'), 'non_negative_numeric', "Accounts Receivable Days")
            _validate_and_store('Inventory_Days', self.get_input_value('inventory_days'), 'non_negative_numeric', "Inventory Days")
            _validate_and_store('AP_Days', self.get_input_value('ap_days'), 'non_negative_numeric', "Accounts Payable Days")
            # Changed to single value input, and key name changed to reflect it
            _validate_and_store('CapExAsPctRevenue', self.get_input_value('capex_as_pct_revenue_pct'), 'numeric', "Capital Expenditures as % of Revenue", is_percentage=True) 
            _validate_and_store('DepreciationRate', self.get_input_value('depreciation_rate_pct'), 'non_negative_numeric', "Depreciation Rate", is_percentage=True)
            _validate_and_store('DividendPayoutRatio', self.get_input_value('dividend_payout_ratio_pct'), 'numeric_range', "Dividend Payout Ratio", is_percentage=True, min_val=0, max_val=100)
            
            # New Advanced Inputs - added to _populate_advanced_assumptions_inputs
            _validate_and_store('TargetMinimumCash', self.get_input_value('target_min_cash'), 'non_negative_numeric', "Target Minimum Cash")
            _validate_and_store('InterestIncomeOnCashRate', self.get_input_value('interest_income_on_cash_rate_pct'), 'non_negative_numeric', "Interest Income on Cash Rate", is_percentage=True)
            _validate_and_store('NewEquityIssued', self.get_input_value('new_equity_issued'), 'non_negative_numeric', "New Equity Issued")
            _validate_and_store('ShareBuybacks', self.get_input_value('share_buybacks'), 'non_negative_numeric', "Share Buybacks")

        # --- Cross-Validation (beyond individual field types) ---
        if 'num_forecast_years' in inputs:
            num_years = inputs['num_forecast_years']
            
            # List fields whose length must match num_forecast_years
            # Only check for lists if not in advanced mode, as advanced mode uses single values for some rates.
            list_fields_to_check = {
                'revenue_growth_rates': "Revenue Growth Rates",
                'cogs_as_pct_revenue_rates': "COGS as % of Revenue",
                'opex_as_pct_revenue_rates': "Operating Expenses as % of Revenue",
            }
            # Remove capex from this check if advanced mode is on, as it's now a single value input
            if not self.advanced_mode_var.get():
                list_fields_to_check['capex_as_pct_revenue_rates'] = "Capital Expenditures as % of Revenue"
            
            for key, field_name in list_fields_to_check.items():
                if key in inputs and isinstance(inputs[key], list) and len(inputs[key]) != num_years:
                    errors.append(f"The number of entries in '{field_name}' ({len(inputs[key])}) must match the 'Number of Forecast Years' ({num_years}).")
        
        # Check if Base Year Equity makes sense (Assets - Liabilities = Equity)
        required_base_data_keys = ['base_cash', 'base_ar', 'base_inventory', 'base_fixed_assets', 'base_ap', 'base_ltd', 'base_retained_earnings', 'base_accumulated_depreciation']
        if all(k in inputs for k in required_base_data_keys):
            total_assets = inputs['base_cash'] + inputs['base_ar'] + inputs['base_inventory'] + (inputs['base_fixed_assets'] - inputs['base_accumulated_depreciation'])
            total_liabilities = inputs['base_ap'] + inputs['base_ltd']
            total_equity = total_assets - total_liabilities
            retained_earnings = inputs['base_retained_earnings']
            share_capital = total_equity - retained_earnings

            # Save computed share capital
            if share_capital < 0:
                errors.append(
                    f"Computed Share Capital is negative based on your inputs: "
                    f"Total Equity ({self.format_currency_output(total_equity, include_symbol=False)}) - "
                    f"Retained Earnings ({self.format_currency_output(retained_earnings, include_symbol=False)}) = "
                    f"{self.format_currency_output(share_capital, include_symbol=False)}. "
                    f"Please enter consistent values."
                )
            else:
                inputs['base_share_capital'] = share_capital  # store computed value for later

        if errors:
            self.display_result("Please correct the following input errors:\n" + "\n".join(errors), is_error=True)
            logger.warning(f"Validation errors: {errors}")
            return

        # --- If all validations pass, proceed to financial model calculation ---
        try:
            # 1. Create the PnL object for the base year from the collected inputs
            base_pnl = PnL(
                Revenue=inputs['base_revenue'],
                COGS=inputs['base_cogs'],
                OperatingExpenses=inputs['base_opex'],
                Depreciation=inputs['base_depreciation'],
                InterestExpense=inputs['base_interest_expense'],
                InterestIncome=0.0, # Assuming no interest income in base year if not explicitly collected
                GrossProfit=inputs['base_revenue'] - inputs['base_cogs'],
                EBIT=(inputs['base_revenue'] - inputs['base_cogs'] - inputs['base_opex'] - inputs['base_depreciation']),
                EBT=0.0, # Placeholder
                Taxes=0.0, # Placeholder
                NetIncome=0.0 # Placeholder
            )
            base_pnl.EBT = base_pnl.EBIT - base_pnl.InterestExpense + base_pnl.InterestIncome
            base_year_tax_rate = inputs['tax_rate'] # Use the general tax rate for base year
            base_pnl.Taxes = base_pnl.EBT * base_year_tax_rate if base_pnl.EBT > 0 else 0.0
            base_pnl.NetIncome = base_pnl.EBT - base_pnl.Taxes


            # 2. Create the BalanceSheet object for the base year from the collected inputs
            base_balance_sheet = BalanceSheet(
                Cash=inputs['base_cash'],
                AccountsReceivable=inputs['base_ar'],
                Inventory=inputs['base_inventory'],
                GrossPPE=inputs['base_fixed_assets'],
                AccumulatedDepreciation=inputs['base_accumulated_depreciation'],
                AccountsPayable=inputs['base_ap'],
                Debt=inputs['base_ltd'],
                ShareCapital=inputs['base_share_capital'],
                RetainedEarnings=inputs['base_retained_earnings'], # This is now Retained Earnings from GUI
                # Derived BS items
                NetPPE=0.0, TotalAssets=0.0, TotalLiabilities=0.0, TotalEquity=0.0, TotalLiabilitiesAndEquity=0.0
            )
            base_balance_sheet.NetPPE = base_balance_sheet.GrossPPE - base_balance_sheet.AccumulatedDepreciation
            base_balance_sheet.TotalAssets = (
                base_balance_sheet.Cash +
                base_balance_sheet.AccountsReceivable +
                base_balance_sheet.Inventory +
                base_balance_sheet.NetPPE
            )
            base_balance_sheet.TotalLiabilities = base_balance_sheet.AccountsPayable + base_balance_sheet.Debt
            base_balance_sheet.TotalEquity = base_balance_sheet.ShareCapital + base_balance_sheet.RetainedEarnings
            base_balance_sheet.TotalLiabilitiesAndEquity = base_balance_sheet.TotalLiabilities + base_balance_sheet.TotalEquity


            # 3. Create the BaseYearData object
            base_year_data = BaseYearData(
                pnl=base_pnl,
                balance_sheet=base_balance_sheet,
                cash=inputs['base_cash']
            )
            
            num_forecast_years = inputs['num_forecast_years']
            
            financial_statements_result: List[FinancialStatements] = []

            if self.advanced_mode_var.get():
                logger.info("Advanced mode is enabled. Preparing AdvancedAssumptions.")

                # Ensure these are float values from lists if applicable, taking the first element
                first_revenue_growth_rate = inputs['revenue_growth_rates'][0]
                first_gross_profit_margin = 1.0 - inputs['cogs_as_pct_revenue_rates'][0]
                first_opex_pct_revenue = inputs['opex_as_pct_revenue_rates'][0]
                
                # Construct the AdvancedAssumptions object
                advanced_assumptions = AdvancedAssumptions(
                    RevenueGrowthRate=first_revenue_growth_rate,
                    GrossProfitMargin=first_gross_profit_margin,
                    OperatingExpenseAsPctRevenue=first_opex_pct_revenue,
                    CapExAsPctRevenue=inputs['CapExAsPctRevenue'], # From single value input
                    DepreciationRate=inputs['DepreciationRate'],
                    AR_Days=inputs['AR_Days'],
                    AP_Days=inputs['AP_Days'],
                    Inventory_Days=inputs['Inventory_Days'],
                    InterestRateOnDebt=inputs['interest_rate'],
                    TaxRate=inputs['tax_rate'],
                    DividendPayoutRatio=inputs['DividendPayoutRatio'],
                    TargetMinimumCash=inputs['TargetMinimumCash'],
                    InterestIncomeOnCashRate=inputs['InterestIncomeOnCashRate'],
                    NewEquityIssued=inputs['NewEquityIssued'],
                    ShareBuybacks=inputs['ShareBuybacks']
                )
                
                logger.info("Calling generate_advanced_financials...")
                financial_statements_result = generate_advanced_financials(
                    base_year_data=base_year_data,
                    assumptions=advanced_assumptions,
                    num_forecast_years=num_forecast_years
                )
            else:
                logger.info("Basic mode is enabled. Preparing Assumptions.")
                # For basic mode, your original Assumptions class likely expects single values
                # If these are lists in basic mode, you need to decide if you want to use the first
                # or if the basic model needs to be adapted for year-specific rates.
                # Assuming single values for now, taking the first from the lists
                first_revenue_growth_rate = inputs['revenue_growth_rates'][0]
                first_gross_profit_margin = 1.0 - inputs['cogs_as_pct_revenue_rates'][0]
                first_opex_pct_revenue = inputs['opex_as_pct_revenue_rates'][0]
                
                # If your basic Assumptions class doesn't have all these fields,
                # you might need to adjust or provide defaults.
                # Assuming 'accounting_basics.py' has an 'Assumptions' class that matches this structure.
                from mathematical_functions.accounting_basics import generate_basic_financials # Ensure this is imported for basic mode
                assumptions_basic = Assumptions(
                    RevenueGrowthRate=first_revenue_growth_rate,
                    GrossProfitMargin=first_gross_profit_margin,
                    OperatingExpenseAsPctRevenue=first_opex_pct_revenue,
                    CapExAsPctRevenue=inputs.get('capex_as_pct_revenue_rates', [0.0])[0] if isinstance(inputs.get('capex_as_pct_revenue_rates'), list) else inputs.get('capex_as_pct_revenue_rates', 0.0), # Assuming list of 1 for basic
                    DepreciationRate=inputs.get('depreciation_rate', 0.0), # This key would only be present if advanced mode was on and it was collected
                    AR_Days=inputs.get('ar_days', 0), # Similarly
                    AP_Days=inputs.get('ap_days', 0), # Similarly
                    Inventory_Days=inputs.get('inventory_days', 0), # Similarly
                    InterestRateOnDebt=inputs['interest_rate'],
                    TaxRate=inputs['tax_rate'],
                    DividendPayoutRatio=inputs.get('dividend_payout_ratio', 0.0) # Similarly
                )

                logger.info("Calling generate_basic_financials...")
                financial_statements_result = generate_basic_financials(
                    base_year_data=base_year_data,
                    assumptions=assumptions_basic,
                    num_forecast_years=num_forecast_years
                )


            self.display_result("Financial statements generated successfully! Results are ready for display.", is_error=False)
            logger.info("Financial statements generation complete.")
            
            if self.controller:
                self.controller._show_frame("Financial Accounting Output", financial_statements_result)
            
        except Exception as e:
            logger.critical(f"An unexpected error occurred during financial model calculation: {e}", exc_info=True)
            self.display_result(f"An unexpected error occurred during calculation: {e}", is_error=True)

    def clear_inputs(self):
        """
        Overrides BaseGUI's clear_inputs to also reset the advanced mode toggle
        and update the UI state.
        """
        super().clear_inputs()
        self.advanced_mode_var.set(False) # Reset advanced mode toggle
        self._toggle_input_sections_visibility() # Update UI based on reset
        self.display_result("All inputs cleared.")


# --- Example Usage (for testing AccountingInputGUI in isolation if desired) ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title(config.MAIN_WINDOW_TITLE + " - Accounting Inputs") # Updated title
    root.geometry(f"{config.DEFAULT_WINDOW_WIDTH}x{config.DEFAULT_WINDOW_HEIGHT}")

    # Apply global styles (as would be done in a main application file)
    style = ttk.Style()
    try:
        style.theme_use(config.TTK_THEME)
    except tk.TclError:
        print(f"Warning: ttk theme '{config.TTK_THEME}' not found. Falling back to 'clam'.")
        style.theme_use('clam') # Fallback if theme isn't available

    # Configure styles based on config.py
    style.configure("InputGUI.TFrame", background=config.COLOR_PRIMARY_BACKGROUND)
    style.configure("Title.TLabel", font=(config.FONT_FAMILY_GENERAL, config.FONT_SIZE_XLARGE, "bold"),
                    foreground=config.COLOR_TEXT_DARK, background=config.COLOR_PRIMARY_BACKGROUND)
    style.configure("Toggle.TCheckbutton", font=(config.FONT_FAMILY_GENERAL, config.FONT_SIZE_MEDIUM),
                    foreground=config.COLOR_TEXT_DARK, background=config.COLOR_PRIMARY_BACKGROUND)
    
    # LabelFrame styling needs separate configurations for the frame and its label
    style.configure("InputSection.TLabelframe", background=config.COLOR_PRIMARY_BACKGROUND,
                    bordercolor=config.COLOR_TEXT_DARK, relief="solid", borderwidth=1)
    style.configure("InputSection.TLabelframe.Label", background=config.COLOR_PRIMARY_BACKGROUND,
                    foreground=config.COLOR_TEXT_DARK, font=(config.FONT_FAMILY_GENERAL, config.FONT_SIZE_LARGE, "bold"))
    
    style.configure("TLabel", background=config.COLOR_PRIMARY_BACKGROUND, foreground=config.COLOR_TEXT_DARK,
                    font=(config.FONT_FAMILY_GENERAL, config.FONT_SIZE_MEDIUM))
    style.configure("TEntry", fieldbackground=config.COLOR_SECONDARY_BACKGROUND, foreground=config.COLOR_TEXT_DARK,
                    font=(config.FONT_FAMILY_GENERAL, config.FONT_SIZE_MEDIUM))
    
    style.map("TButton",
              background=[('active', config.COLOR_ACCENT_HOVER), ('!active', config.COLOR_ACCENT_BLUE)],
              foreground=[('active', config.COLOR_TEXT_LIGHT), ('!active', config.COLOR_TEXT_LIGHT)])
    style.configure("TButton", font=(config.FONT_FAMILY_GENERAL, config.FONT_SIZE_MEDIUM, "bold"),
                    background=config.COLOR_ACCENT_BLUE, foreground=config.COLOR_TEXT_LIGHT,
                    padding=6, relief="flat") # Use "flat" for modern look


    # Create and pack the AccountingInputGUI instance
    accounting_input_gui = AccountingInputGUI(root)
    accounting_input_gui.pack(fill="both", expand=True)

    root.mainloop()