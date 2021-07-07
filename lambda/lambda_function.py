# -*- coding: utf-8 -*-
# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils
import os
import json
import requests
import calendar
from datetime import datetime
from pytz import timezone
from ask_sdk_s3.adapter import S3Adapter
s3_adapter = S3Adapter(bucket_name=os.environ["S3_PERSISTENCE_BUCKET"])
#from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
#auth = session.post(hostname)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to Optus! What is your contact ID?"
        reprompt_text = "What is your contact ID?"
        logger.info('greeting user and waiting for contact id')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class CaptureContactIdIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CaptureContactIdIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In the capture contact id intent handler")
        slots = handler_input.request_envelope.request.intent.slots
        contactid = slots["contact_id"].value
        logger.info("user provided {contact_id} in intent".format(contact_id=contactid))
        # get cust id from profile controller
        session = requests.Session()
        session.auth = ('hackathon.user', 'hopr03owpkielsifltie9')
        hostname = "https://express-it.optusnet.com.au/et-hackathon-api"
        response = session.get(hostname + '/customers/{contactid}'.format(contactid=contactid))
        payload_response = json.loads(response.text)
        firstname = payload_response["firstName"]
        # save into profile/persistence 
        attributes_manager = handler_input.attributes_manager
        customer_attributes = { "contactid": contactid, "firstname":firstname }
        attributes_manager.persistent_attributes = customer_attributes
        attributes_manager.save_persistent_attributes()
        speak_output = "Thank you! I will remember your contact ID {firstname}".format(firstname=firstname)
        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )

class HasContactIdLaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # check if id exsits and prompt accordingly 
        attr = handler_input.attributes_manager.persistent_attributes
        #contactid = attr['contactid']
        isPresent = 'contactid' in attr
        return isPresent and ask_utils.is_request_type("LaunchRequest")(handler_input)
    def handle(self, handler_input):
        logger.info("found customer info. waiting for a response")
        # continue to making recommendations or waiting for further intent from user
        attr = handler_input.attributes_manager.persistent_attributes
        firstname = attr['firstname']
        speak_output = "<amazon:domain name=\"fun\">Hi {firstname}! Welcome back to Optus!</amazon:domain>".format(firstname=firstname)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GetRecommendationIntentHandler(AbstractRequestHandler): 
    def can_handle(self, handler_input):
        # confirm you can handle input 
        return ask_utils.is_intent_name("GetRecommendationIntent")(handler_input)
        
    def handle(self, handler_input): 
        # get the recommendation using the contact id - call the amazon personalize API to get the recommendation 
        # for now hardcoded but to be replaced by the personalize API 
        #TODO
        logger.info("making recommendation")
        recommendation = "Ring Video Doorbell 4"
        category = "security"
        # make the recommendation to the user - build the sentence for the recommendation 
        speak_output = ""
        if category == "security":
            speak_output = "<p>I'd recommend a {recommendation} so that you always know when your next amazing online order arrives.</p>".format(recommendation=recommendation)
        elif category == "connectivity": 
            speak_output = "<p>I'd recommend an {recommendation} for all your smart devices at home.</p>".format(recommendation=recommendation)
        else: 
            speak_output = "<p>How about {recommendation} product to get started with your smart home needs?</p>"
            
        reprompt_text = "<p>Would you like us to organise the purchase for you?</p>"
        speak_output = speak_output + " " + reprompt_text
        # reprompt/ask to wait for confirmation - over to orderintenthandler 

        # save the recommendation in memory 
        attributes_manager = handler_input.attributes_manager
        attr = attributes_manager.persistent_attributes
        attr["recommendation"] = recommendation
        attributes_manager.persistent_attributes = attr
        attributes_manager.save_persistent_attributes()
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class SubmitOrderIntentHandler(AbstractRequestHandler): 
    def can_handle(self, handler_input):
        # confirm you can handle input 
        return ask_utils.is_intent_name("SubmitOrderIntent")(handler_input)
        
    def handle(self, handler_input): 
        # user confirmed they wish to order. Start confirming delivery location and payment 
        logger.info("submitting the order ")
        speak_output = '<amazon:emotion name=\"excited\" intensity=\"high\">Great!</amazon:emotion> would you like us to add this to your optus bill and deliver it to your home address?'
        reprompt_text = "Would like to continue ordering the product?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt_text)
                .response
        )

class OrderConfirmationIntentHandler(AbstractRequestHandler): 
    def can_handle(self, handler_input):
        # confirm you can handle input 
        return ask_utils.is_intent_name("OrderConfirmationIntent")(handler_input)
        
    def handle(self, handler_input): 
        # user confirmed home delivery and optus bill process
        # submit the order and get the address details from API
        #TODO 
        attributes_manager = handler_input.attributes_manager
        attr = attributes_manager.persistent_attributes
        recommendation = attr["recommendation"]
        logger.info("order confirmation")
        speak_output = "Thats all done! Your {recommendation} will be delivered to <say-as interpret-as=\"address\">123 fake st</say-as> and we'll sms your tracking details shortly.".format(recommendation=recommendation)
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )
    
class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"
        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        # Any cleanup logic goes here.
        return handler_input.response_builder.response
        
class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)
    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."
        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )
        
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True
    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        speak_output = "Sorry, I had trouble doing what you asked. Please try again."
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.
#sb = SkillBuilder()
sb = CustomSkillBuilder(persistence_adapter=s3_adapter)

sb.add_request_handler(HasContactIdLaunchRequestHandler())
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CaptureContactIdIntentHandler())
sb.add_request_handler(GetRecommendationIntentHandler())
sb.add_request_handler(SubmitOrderIntentHandler())
sb.add_request_handler(OrderConfirmationIntentHandler())


# default handlers out of the box 
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_exception_handler(CatchAllExceptionHandler())
lambda_handler = sb.lambda_handler()