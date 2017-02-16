import tasks
import logging

logging.basicConfig(level=logging.DEBUG)

tasks.create_tables()

tasks.initialize_nft()