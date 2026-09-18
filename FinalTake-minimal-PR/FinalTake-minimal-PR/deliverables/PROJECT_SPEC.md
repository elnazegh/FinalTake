# FinalTake Project Specification

## Project Summary
FinalTake is a social entertainment web application where users can discover, rate, and review movies, TV shows, books, and video games. The application combines a searchable media catalog with community reviews and user accounts.

## Semester Goal
Deliver a working full-stack prototype that supports account creation/login, media discovery, media detail pages, ratings/reviews, and a maintainable MySQL-backed data layer.

## Core Functional Requirements
1. Users can create an account and log in.
2. Users can browse and search media across movies, TV, books, and games.
3. Users can view details for a media item.
4. Authorized users can add new media entries.
5. Users can submit one rating/review per media item and later update it.
6. Media detail pages display aggregate rating data and community reviews.
7. The application persists users, media, and reviews in MySQL.

## Non-Functional Requirements
- Use parameterized SQL queries.
- Keep database access separated from HTTP route handling.
- Protect credentials through environment variables rather than source control.
- Validate incoming API data and return consistent HTTP errors.
- Maintain a schema that enforces referential integrity with foreign keys.
- Provide basic automated tests for backend routes.

## Current Technical Direction
- Frontend: HTML, CSS, JavaScript (existing repository)
- Backend: Python 3 + Flask
- Database: MySQL 8+
- Data access: mysql-connector-python with repository-style modules
- Testing: pytest
- Version control: Git/GitHub with feature branches and pull requests
