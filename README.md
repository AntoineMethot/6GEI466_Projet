# 6GEI466_Projet

# Horoscope Web Application

## Description

Cette application web permet aux utilisateurs de consulter leur **horoscope quotidien** via une architecture **frontend / backend**. Les utilisateurs se connectent grâce à un système **SSO (Single Sign-On)** avec un fournisseur externe (ex. Google ou Microsoft). Une fois authentifiés, ils peuvent générer leur horoscope selon leur signe astrologique, consulter l’historique de leurs horoscopes et laisser des commentaires.

Les horoscopes sont récupérés à partir d’une **API externe**, puis sauvegardés dans une **base de données NoSQL** avec les commentaires associés.

---

## Technologies

**Frontend**
- HTML
- CSS
- Bootstrap
- JavaScript

**Backend**
- Python
- Flask (API REST)

**Authentification**
- OAuth / OpenID Connect (SSO)

**Base de données**
- NoSQL (ex. MongoDB)

---

## Fonctionnalités

- Connexion via **SSO**
- Génération d’horoscope par **signe astrologique**
- Récupération des données via **API externe**
- Sauvegarde des horoscopes dans la base de données
- Consultation de l’**historique des horoscopes**
- **Commentaires** sur les horoscopes
- Recapitulatif sur l'exactitude des horoscopes