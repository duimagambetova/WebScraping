This script scrapes data from the Kazakh website Surak Baribar using Selenium and saves the data in JSON format. 

It uses multithreading to handle multiple pages simultaneously, improving the efficiency of the scraping process.

Data Format
The script retrieves data in the following format:

answers.append({
    "text": answer_text,
    "date": answer_date,
    "upvotes": int(answer_upvotes)
})

page_data.append({
    "question_title": question_title,
    "question_content": question_content,
    "question_date": question_date,
    "question_tag": category_text,
    "question_views": int(view_count),
    "question_upvotes": int(upvote_count),
    "answers": answers
})
Each page with 25 questions is extracted into one separate file in the data folder.

Logs
logs.txt: Contains error logs and information about any issues encountered during the scraping process.


