## [Tengrinews](https://tengrinews.kz/) parser.
Project to parse news site "Tengrinews", 
and save it in mysql database.

## Get start.
- Install dependencies  from requirements.txt.
- Create database in "mysql" version 8.0.21.
- Create two db models: item, comments.
#### item model fields and types:
- id - smallint 
- news_link - varchar(255)
- title - text
- content - text
- publish_date - date
- publish_datetime - datetime
- parse_date - datetime

#### comments model fields and type:
- id - smallint
- item_id - smallint
- author - varchar(100)
- date - datetime
- comment - text
- parse_date - datetime

## Motivation

Task for job assignment.


