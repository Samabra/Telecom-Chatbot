# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import json
import os
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.events import ActionExecuted
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction

class ActionDefaultFallback(Action):
    def name(self) -> str:
        return "action_default_fallback"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Sorry, I didn't understand that. Can you please clarify?")
        return []



class AccountService:
    instance = None
    accounts = None
    DEFAULT_FILE_PATH = "exampleData/accountData.json"


    ## Follows Singleton Pattern so there is only one instance to retrieve account
    ## details

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(AccountService, cls).__new__(cls)
        return cls.instance
    
    ## Initiate a new class iff there is no instance

    def __init__(self, filePath=None):
        if AccountService.accounts is None:
            self.filePath = filePath or self.findFile()
            AccountService.accounts = self.loadAccounts()


    ## Finds files according to the default path
    ## This path is due to the fact that only local example data 
    ## in JSON was used
    def findFile(self):
        currentDir = os.path.dirname(__file__)
        potentialPaths = [
            os.path.join(currentDir, self.DEFAULT_FILE_PATH),
        ]
        for path in potentialPaths:
            if os.path.exists(path):
                return path
        raise FileNotFoundError(f"File for account data not found in expected locations: {potentialPaths}")
    

    ## Loads accounts from the exampleData.json file
    def loadAccounts(self):
        try:
            with open(self.filePath, 'r') as file:
                data = json.load(file)
            if not isinstance(data, dict) or "accounts" not in data:
                raise ValueError("Error: Account data file must contain an 'accounts' key.")
            return data["accounts"]
        except FileNotFoundError:
            print("Warning: Account data file is missing.")
            return None
        except json.JSONDecodeError:
            raise ValueError("Error: Account data file is not a valid JSON file.")


    ## Get the specific account details of a customer
    def getAccount(self, account_details):
        if AccountService.accounts is None:
            return None
    
        return next(
            (
                acc for acc in AccountService.accounts
                if isinstance(acc, dict) and
                ( 
                    acc.get("account_id") == account_details
                    or acc.get("email", "").lower() == account_details.lower()
                    or acc.get("phone_number", "") == account_details
                )
            ),
            None
        )
    
    def validateAccountDetails(self, account_details):
        if AccountService.accounts is None:
            return None
        
        if account_details:
            return any (
                acc.get("account_id") == account_details
                or acc.get("email", "").lower() == account_details.lower()
                or acc.get("phone_number", "") == account_details
                for acc in AccountService.accounts
            )
        return False
    ## Save the account after any change to the exampleJSON data file
    def saveAccounts(self):
        try:
            with open(self.filePath, 'w') as file:
                json.dump(self.accounts, file, indent=4)
        except Exception as e:
            print(f"Error occured while saving the accounts: {e}")


    def getAccountBalance(self, account_details):
        account = self.getAccount(account_details)
        return account["balance"] if account else None

    def getAccountName(self, account_details):
        account = self.getAccount(account_details)
        return account["name"] if account else None
    
    def getAccountEmail(self, account_details):
        account = self.getAccount(account_details)
        return account["email"] if account else None
    
    def getAccountPlan(self, account_details):
        account = self.getAccount(account_details)
        return account["plan"] if account else None
    
    def getAccountPhoneNumber(self, account_details):
        account = self.getAccount(account_details)
        return account["phone_number"] if account else None
    
    def getAccountBillingHistory(self, account_details):
        account = self.getAccount(account_details)
        return account["billing_history"] if account else None
    
    def getAccountPaymentMethod(self, account_details):
        account = self.getAccount(account_details)
        return account["payment_methods"] if account else None
    
    def isExistingPayment(self, checkMethod, account_details):
        account = self.getAccount(account_details)
        
        if account is None:
            return "You do not seem to have an account, would you like to make one?"
        return any(method['method'].lower == checkMethod.lower() for method in account["payment_methods"])

    def getCurrentPaymentMethod(self, account_details):
        account = self.getAccount(account_details)

        if account is None:
            return "You do not seem to have an account, would you like to make one?"
        
        currentMethod = next((method for method in account['payment_methods'] if method['default']), None)
        return currentMethod
    
    def changePaymentMethod(self, currentMethod, newMethod, account_details):
        account = self.getAccount(account_details)

        if account is None:
            return "Account not found."
        
        if not self.isExistingPayment(currentMethod, account_details):
            return f"Payment method {currentMethod} is not found for this account. Please try again or you can add this as a payment method."
        
        if self.isExistingPayment(newMethod, account_details):
            return f"Payment method {newMethod} is already a payment method, would you like to switch to it instead?"
        
        account["payment_methods"].remove(currentMethod)
        account["payment_methods"].append(newMethod)

        self.saveAccounts()
        return f"Payment method {currentMethod} has been changed to {newMethod}."

    def switchPaymentMethod(self, currentMethod, otherMethod, account_details):
        if currentMethod.lower() == otherMethod.lower():
            return f"This is already your current method of payment."
        
        account = self.getAccount(account_details)

        if account is None:
            return "Account not found. Would you like to make one?"
        
        if not self.isExistingPayment(currentMethod, account_details):
            return f"Payment method {currentMethod} is not found for this account. You can try again or add this payment method to your account."
        
        if not self.isExistingPayment(otherMethod, account_details):
            return f"Cannot switch to the proposed method {otherMethod} as it is not an existing method. Please try again or add this payment method to your account."

        currentPayment = next(method for method in account["payment_methods"] if method["method"].lower() == currentMethod.lower())
        otherPayment = next(method for method in account["payment_methods"] if method["method"].lower() == otherPayment.lower())
        
        currentPayment["default"] = False
        otherPayment["default"] = True

        self.saveAccount()

        return f"Payment method has been switched from '{currentMethod}' to '{otherMethod}'."
    
    def addPaymentMethod(self, newMethod, account_details):
        account = self.getAccount(account_details)

        if account is None:
            return "You do not seem to have an account, would you like to make one?"
        
        if self.isExistingPayment(newMethod, account_details):
            return f"Payment method {newMethod} is already a payment method, would you like to switch to it instead."
        
        account["payment_methods"].append({"method": newMethod, "details": "New payment details", "default": False})
        

        self.saveAccount()

        return f"New payment method has been added."
    
    def removePaymentMethod(self, removeMethod, account_details):
        account = self.getAccount(account_details)

        if account is None:
            return "You do not seem to have an account, would you like to make one?"
        
        if not self.isExistingPayment(removeMethod, account_details):
            return f"This is not an existing payment method. Please try again."
        
        account["payment_methods"].remove(removeMethod)

        self.saveAccount()

        return f"Payment method has been successfully removed."
    
    def planChange(self, newPlan, account_details):
        account = self.getAccount(account_details)

        if not account:
            return f"We could not change your plan as you do not seem to have an account. Would you like to make an account?"
        
        account["plan"] = newPlan

        self.saveAccount()

        return f"Successfully updated your plan to {newPlan}. We hope you are satisfied by your new plan."



class Plans:
    instance = None
    plans = None
    DEFAULT_FILE_PATH = "exampleData/plans.json"


    ## Follows Singleton Pattern so there is only one instance to retrieve plan
    ## details

    def __new__(cls, *args, **kwargs):
        if not cls.instance:
            cls.instance = super(Plans, cls).__new__(cls)
        return cls.instance
    
    ## Initiate a new class iff there is no instance

    def __init__(self, filePath=None):
        if Plans.plans is None:
            self.filePath = filePath or self.findFile()
            self.plans = self.loadPlans()
    
    def loadPlans(self):
        try:
            with open(self.filePath, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Error: Account data file is missing.")
        except json.JSONDecodeError:
            raise ValueError("Error: Account data file is not a valid JSON file.")


    def getPlans(self):
        if not self.plans:
            return None
        else:
            return self.plans
    
    def getPlanDetails(self, planName):
        plans = self.getPlans()

        if not plans:
            return "There are currently no available plans."
        
        for plan in self.plans.get("plans", []):
            if plan["name"].lower() == planName.lower():
                planDetails = plan["description"]
                features = plan["features"]
                formattedFeatures = "\n".join(f"{key.capitalize()}: {value}" for key, value in features.items())
                return f"{planName.capitalize()} Plan Details: \n\n Features:\n{formattedFeatures}"
        return f"The {planName.capitalize()} plan is currently not available."
    

    def getBasicPlan(self):
        return self.getPlanDetails("Basic")

    def getPremiumPlan(self):
        return self.getPlanDetails("Premium")
    
    def getUnlimitedPlan(self):
        return self.getPlanDetails("Unlimited")
    
    def getFamilyPlan(self):
        return self.getPlanDetails("Family")
    
    def getGroupPlan(self):
        return self.getPlanDetails("Group")
    
    def getPrepaidPlan(self):
        return self.getPlanDetails("Prepaid")
    
    def getPostpaidPlan(self):
        return self.getPlanDetails("Postpaid")
    
    def getDataOnlyPlan(self):
        return self.getPlanDetails("Data-Only")
    
    def getInternationalPlan(self):
        return self.getPlanDetails("International")
    
    def getStudentPlan(self):
        return self.getPlanDetails("Student")

    def getSeniorPlan(self):
        return self.getPlanDetails("Senior")

    
    
class ValidateAccountDetails(FormValidationAction):
    MAX_RETRIES = 5
    def name(self) -> str:
        return "validate_account_details_form"
    def validateAccountDetails(self, slot_value: str, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict) -> dict:
        account_details = tracker.get_slot("account_details")
        retryAttempts = tracker.get_slot("retry_attempts") or 0

        if retryAttempts >= MAX_RETRIES:
            dispatcher.utter_message(text="I'm unable to verify your account details after multiple attempts.")
        if not slot_value:
            dispatcher.utter_message(text="You have not provided any account details.")
            retryAttempts += 1
            return {"account_details": None, "retry_attempts": retryAttempts + 1}

       
        accountService = AccountService()
        if accountService.validateAccountDetails(slot_value):
            return {"account_details": slot_value}
        else:
            dispatcher.utter_message(text="Your account details may be incorrect or no account exists with these details.")
            return {"account_details": None, "retry_attempts": retryAttempts + 1.0}



class ActionAccountBalance(Action):
    def name(self) -> str:
        return "action_show_balance_amount"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        account_details = tracker.get_slot("account_details")
        
        if account_details is None:
            dispatcher.utter_message(text="Your account ID, email or phone number is required to be able to access your account details.")
            return []

        accountService = AccountService()
        balance = accountService.getAccountBalance(account_details)

        if balance is not None:
            dispatcher.utter_message(text=f"Your current balance is ${balance: .2f},")
            return []
        
        dispatcher.utter_message(text=" I couldn't retrieve your balance. Please try again later.")


class ActionBillingHistory(Action):
    def name(self) -> str:
        return "action_view_billing_history"
    
    def run(self, dispatcher, tracker, domain):
        account_details = tracker.get_slot('account_details')
        financialYear = tracker.get_slot('financial_year')
        month = tracker.get_slot('month')
        year = tracker.get_slot('year')
        email = tracker.get_slot("email")
        phone_number = tracker.get_slot("phone_number")

        if not ValidateAccountDetails.validateAccountDetails(tracker):
            dispatcher.utter_message(text="I require either your account ID, email or phone number is required for me to show your billing history.")
            return []

        accountService = AccountService()
        billingHistory = accountService.getAccountBillingHistory(account_details)

        if billingHistory is None:
            dispatcher.utter_message(text="Sorry, I couldn't retrieve your billing history")
            return []
        
        
        filteredBills = []
        currentDate = datetime.now()

        if not financialYear and not year and not month:
            startDate = f"01-01-{currentDate.year}"
            endDate = currentDate

        elif financialYear:
            startYear - int(financialYear) - 1
            startDate = datetime(startYear, 7, 1)
            endDate = datetime(int(financialYear), 6, 30)

        elif year:
            startDate = datetime(int(year), 1, 1)
            endDate = datetime(int(year), 12, 31)
        
        elif month:
            monthNumber = datetime.strptime(month, "%B").month
            startDate = datetime(currentDate.year, monthNumber, 1)
            endDate = startDate + timedelta(days=32 - startDate.day)
        
        for bill in billingHistory:
            billDate = datetime.strptime(bill['date'], "%d-%m-%Y")
            if startDate <= billDate <= endDate:
                filteredBills.append(bill)

        if not filteredBills:
            dispatcher.utter_message(text="There doesn't seem to be any billing history for the selected time period.")
        
        message = "Here is your billing history:\n"
        for bill in filteredBills:
            message += f"- {bill['date']}: {bill['description']} - ${bill['amount']}\n"
        dispatcher.utter_message(text=message)
        return []



class PaymentValidator:
    VALID_PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal"]
    
    def isValidPayment(requestedMethod):
        return requestedMethod.lower() in (method.lower() for method in PaymentValidator.VALID_PAYMENT_METHODS)
    
    def suggestValidMethods():
        return PaymentValidator.VALID_PAYMENT_METHODS



class CurrentPayment(Action):
    def name(self) -> str:
        return "action_current_payment_method"
    
    def run(self, dispatcher, tracker, domain):
        account_details = tracker.get_slot("account_details")
        if not ValidateAccountDetails.validateAccountDetails(tracker):
            dispatcher.utter_message(text="To view your current payment details, I need either your account ID, email or phone number.")
            return []

        accountService = AccountService()
        currentPaymentMethod = accountService.getCurrentPaymentMethod(account_details)
        
        if not currentPaymentMethod:
            return f"You do not seem to have a payment method set for this account. Would you like to add one?"
        
        return f"Your current payment method is '{currentMethod['method']}' with details: {currentMethod['details']}."


class ChangePayment(Action):
    def name(self) -> str:
        return "action_change_payment_method"
    
    def run(self, dispatcher, tracker, domain):
        account_details = tracker.get_slot("account_details")
        currentMethod = tracker.get_slot("current_method")
        newMethod = tracker.get_slot("new_method")

        if not ValidateAccountDetails.validateAccountDetails(tracker):
            dispatcher.utter_message(text="To change your payment options, I need your either your account ID, email or phone number.")
            return []

        paymentValidator = PaymentValidator()
    

        if not paymentValidator.isValidPayment(currentMethod):
            dispatcher.utter_message(text=f"{currentMethod.capitalize()} is not your current payment method.")
            return []
        
        if not paymentValidator.isValidPayment(newMethod):
            dispatcher.utter_message(text=f"{newMethod.capitalize()} is not a valid payment method.")
            return []

        
        accountService = AccountService()
        message = accountService.changePaymentMethod(currentMethod, newMethod, account_details)

        dipatcher.utter_message(text=message)
        return []

class SwitchPayment(Action):
    def name(self) -> str:
        return "action_switch_payment_method"
    
    def run(self, dispatcher, tracker, domain):
        account_details = tracker.get_slot("account_details")
        currentMethod = tracker.get_slot("current_method")
        otherMethod = tracker.get_slot("other_method")

        if not ValidateAccountDetails.validateAccountDetails(tracker):
            dispatcher.utter_message(text="To switch your payment options, I need your either your account ID, email or phone number.")
            return []

        paymentValidator = PaymentValidator()
        
        if not paymentValidator.isValidPayment(currentMethod):
            return f"{currentMethod.capitalize()} is not your current payment method."
        
        if not paymentValidator.isValidPayment(otherMethod):
            return f"{otherMethod.capitalize()} is not a payment set up with your account."

        accountService = AccountService()
        message = accountService.switchPaymentMethod(currentMethod, otherMethod, account_details)
        dipatcher.utter_message(text=message)
        return []



class AddPayment(Action):
    def name(self) -> str:
        return "action_add_payment_method"
    
    def run(self, dispatcher, tracker, domain):
        account_details = tracker.get_slot("account_details")
        newMethod = tracker.get_slot("new_method")

        if not ValidateAccountDetails.validateAccountDetails(tracker):
            dispatcher.utter_message(text="To add more payment options, I need your either your account ID, email or phone number.")
            return []


        paymentValidator = PaymentValidator()

        if not paymentValidator.isValidPayment(newMethod):
            return f"{newMethod.capitalize()} is not a valid payment."

        accountService = AccountService()
        message = accountService.addPaymentMethod(newMethod, account_details)
        dipatcher.utter_message(text=message)
        return []

class RemovePayment(Action):
    def name(self) -> str:
        return "action_remove_payment_method"
    
    def run(self, dispatcher, tracker, domain):
        account_details = tracker.get_slot("account_details")
        removeMethod = tracker.get_slot("remove_method")
        if not ValidateAccountDetails.validateAccountDetails(tracker):
            dispatcher.utter_message(text="To remove any payment options, I need your either your account ID, email or phone number.")
            return []


        paymentValidator = PaymentValidator()

        if not paymentValidator.isValidPayment(removeMethod):
            return f"We cannot remove {removeMethod.capitalize()} as it is not a valid payment method."

        accountService = AccountService()
        message = accountService.removePaymentMethod(removeMethod, account_details)
        dipatcher.utter_message(text=message)
        return []



class ChangePlans(Action):
    def name(self) -> str:
        return "action_change_plan"
    
    def run(self, dispatcher, tracker, domain):
        account_details = tracker.get_slot("account_details")
        newPlan = tracker.get_slot("new_plan")
        if not ValidateAccountDetails.validateAccountDetails(tracker):
            dispatcher.utter_message(text="In order to change the plan associated with your account, I need your either your account ID, email or phone number.")
            return []

        accountService = AccountService()
        message = accountService.planChange(newPlan, account_details)
        dipatcher.utter_message(text=message)
        return []


class GetBasicPlanDetails(Action):
    def name(self) -> str:
        return "action_basic_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getBasicPlan()
        dispatcher.utter_message(text=message)
        return []

class GetPremiumPlanDetails(Action):
    def name(self) -> str:
        return "action_premium_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getPremiumPlan()
        dispatcher.utter_message(text=message)
        return []

class GetUnlimitedPlanDetails(Action):
    def name(self) -> str:
        return "action_unlimited_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getUnlimitedPlan()
        dispatcher.utter_message(text=message)
        return []

class GetFamilyPlanDetails(Action):
    def name(self) -> str:
        return "action_family_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getFamilyPlan()
        dispatcher.utter_message(text=message)
        return []

class GetGroupPlanDetails(Action):
    def name(self) -> str:
        return "action_group_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getGroupPlan()
        dispatcher.utter_message(text=message)
        return []


class GetPrepaidPlanDetails(Action):
    def name(self) -> str:
        return "action_prepaid_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getPrepaidPlan()
        dispatcher.utter_message(text=message)
        return []


class GetPostpaidPlanDetails(Action):
    def name(self) -> str:
        return "action_postpaid_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getPostpaidPlan()
        dispatcher.utter_message(text=message)
        return []


class GetDataOnlyPlanDetails(Action):
    def name(self) -> str:
        return "action_get_data_only_plan"

    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getDataOnlyPlan()
        dispatcher.utter_message(text=message)
        return []


class GetInternationalPlanDetails(Action):
    def name(self) -> str:
        return "action_get_international_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getInternationalPlan()
        dispatcher.utter_message(text=message)
        return []



class GetStudentPlanDetails(Action):
    def name(self) -> str:
        return "action_student_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getStudentPlan()
        dispatcher.utter_message(text=message)
        return []


class GetSeniorPlanDetails(Action):
    def name(self) -> str:
        return "action_senior_plan"
    
    def run(self, dispatcher, tracker, domain):
        plans = Plans()
        message = plans.getSeniorPlan()
        dispatcher.utter_message(text=message)
        return []