import tasks
import logging

logging.basicConfig(level=logging.DEBUG)

tasks.create_tables(database='static')

tasks.initialize_nft(database='static')