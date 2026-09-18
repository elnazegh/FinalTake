# Git instructions

From a clean checkout of the latest shared repository, create a feature branch before applying these files:

```bash
git checkout -b feature/database-backend-sprint1-merge
# copy/reconcile the packaged files into the checkout
git add .
git commit -m "Integrate media database and API with Sprint 1 backend"
git push -u origin feature/database-backend-sprint1-merge
```

Open a pull request into the team's current integration branch rather than pushing directly to main.
