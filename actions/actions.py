from elasticsearch import Elasticsearch
from transformers import pipeline, BertTokenizerFast, BertForQuestionAnswering
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ActionSearchDocument(Action):

    def name(self) -> str:
        return "action_search_document"

    def __init__(self):
        # Initialize Elasticsearch with authentication (optional)
        self.es = Elasticsearch("http://192.168.1.31:9200", http_auth=('elastic', 'dJu7Ub1jYsvj622vMHiA'))

        # Initialize BERT model and tokenizer for question answering
        self.tokenizer = BertTokenizerFast.from_pretrained('bert-base-cased')
        self.model = BertForQuestionAnswering.from_pretrained('bert-base-cased')
        self.qa_pipeline = pipeline('', model=self.model, tokenizer=self.tokenizer)

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        # Get user query from the tracker
        user_query = tracker.latest_message.get('text')

        logger.debug("TESTING THE LOG======")

        # Step 1: Search Elasticsearch for documents related to the user query
        documents = self.search_documents(user_query)

        logger.debug(f"Documents before--- {documents}")
        if not documents:
            dispatcher.utter_message(text="Sorry, I couldn't find any relevant documents.")
            return []
        logger.debug(f"Documents after--- {documents}")
        # Step 2: Use BERT to find the best answer from the retrieved documents
        best_answer = None
        for doc in documents:
            # Assuming content is inside 'attachment.content'
            context = doc['_source'].get('attachment', {}).get('content', "")
            logger.debug(f"Context--- {context}")
            if not context:
                context = doc['_source'].get('content', "")  # Fallback if 'attachment.content' is empty

            answer = self.get_answer_from_document(user_query, context)

            logger.debug(f"Answer--- {answer}")
            if answer:
                best_answer = f"Answer: {answer}\nFound in document: {doc['_source'].get('title', 'No Title')}"
                break

        if best_answer:
            dispatcher.utter_message(text=best_answer)
        else:
            dispatcher.utter_message(text="Sorry, I couldn't find a precise answer.")

        return []

    def search_documents(self, user_query):
        logger.debug("testing the logs")
        # Step 1: Elasticsearch query optimized for both phrase matching and standard matching
        search_query = {
            # "query": {
            #     "bool": {
            #         "should": [
            #             {"match_phrase": {"attachment.content": user_query}},
            #             {"match": {"title": user_query}},
            #             {"match": {"content": user_query}}  # Regular content match
            #         ]
            #     }
            # },
            "query": {
                "multi_match": {
                    "query": user_query,
                    "fields": ["title", "content", "attachment.content"],
                    "fuzziness": "AUTO",
                    "operator": "or"
                }
            },
            "size": 5  # Limit the number of results for performance reasons
        }

        # Step 2: Search in Elasticsearch index
        response = self.es.search(index="new_policy_documents", body=search_query)
        # logger.debug(f"TESTING THE LOG======{response[]}")
        return response['hits']['hits']

    def get_answer_from_document(self, question, context):
        logger.debug(f"question: {question}, {context}")
        # Step 3: Use BERT to find the best answer within the document's content
        try:
            result = self.qa_pipeline({
                'question': question,
                'context': context
            })
            logger.debug(f"Result: {result}")
            return result['answer']
        except Exception as e:
            logger.debug(f"Error: {e}")
            print(f"Error finding answer: {e}")
            return None
