# Guide MCP Odoo x Claude — Ce que vous pouvez faire

> **Mode : YOLO = true (lecture + ecriture)**
> Ce document decrit les actions que Claude peut realiser dans votre instance Odoo via le serveur MCP.
> Il s'adresse aux utilisateurs metier qui interagissent avec Odoo depuis Claude.

---

## Comment ca marche ?

Claude se connecte a votre Odoo via 4 operations de base :

| Operation | Description |
|---|---|
| **Rechercher** | Trouver des enregistrements selon des criteres (nom, date, statut...) |
| **Consulter** | Lire le detail d'un enregistrement precis |
| **Creer** | Ajouter un nouvel enregistrement |
| **Modifier** | Mettre a jour un enregistrement existant |
| **Supprimer** | Effacer un enregistrement |

---

## Contacts & Annuaire

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Chercher un client ou fournisseur | *"Trouve-moi le contact Tarek BOURAHLI"* |
| Voir les coordonnees d'un contact | *"Donne-moi le telephone et l'email de Aicha BENZAZA"* |
| Lister les contacts d'une ville ou pays | *"Liste tous les contacts a Alger"* |
| Creer un nouveau contact | *"Cree un contact : Mohamed Ali, tel 0555123456, Oran"* |
| Modifier un contact | *"Mets a jour l'email de Ihcene MENOUS"* |
| Voir les comptes bancaires d'un partenaire | *"Quels sont les RIB enregistres pour 1161 Studio ?"* |

---

## CRM — Prospection commerciale

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Voir toutes les opportunites en cours | *"Montre-moi le pipeline commercial"* |
| Filtrer par etape (Nouveau, Qualifie, Gagne...) | *"Quelles opportunites sont au stade Qualifie ?"* |
| Voir le chiffre d'affaires attendu | *"Quel est le CA prevu sur les opportunites ouvertes ?"* |
| Creer une opportunite | *"Cree une opportunite : Villa Zeralda, client Mehdi S, montant 2 000 000 DA"* |
| Modifier une opportunite | *"Passe l'opportunite Villa Golf au stade Gagne"* |
| Voir les activites planifiees | *"Quelles sont les prochaines relances CRM ?"* |

---

## Ventes — Devis & Commandes

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Lister les devis en brouillon | *"Quels devis ne sont pas encore confirmes ?"* |
| Voir le detail d'une commande | *"Montre-moi la commande Villa M - Briquetage"* |
| Voir les lignes d'une commande | *"Quels sont les postes du devis S00066 ?"* |
| Creer un devis | *"Cree un devis pour Tarek BOURAHLI avec une ligne : Fondations, 500 000 DA"* |
| Modifier un devis | *"Change le montant de la ligne 1 du devis S00068 a 750 000 DA"* |
| Chercher les ventes d'un client | *"Combien de commandes a-t-on fait pour Aicha BENZAZA ?"* |
| Voir les commissions | *"Montre les plans de commission actifs"* |

---

## Comptabilite & Facturation

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Lister les factures clients | *"Montre toutes les factures de 2026"* |
| Voir les factures impayees | *"Quelles factures sont en attente de paiement ?"* |
| Voir le detail d'une facture | *"Donne-moi le detail de la facture Villa M - Briquetage"* |
| Creer une facture brouillon | *"Cree une facture brouillon pour Tarek BOURAHLI, montant 1 500 000 DA"* |
| Consulter les paiements recus | *"Liste les paiements recus ce mois"* |
| Voir les comptes comptables | *"Montre le plan comptable"* |
| Consulter les journaux | *"Quels journaux comptables existent ?"* |
| Voir les budgets | *"Quel est le budget prevu vs realise ?"* |
| Consulter les releves bancaires | *"Montre les derniers releves bancaires importes"* |

---

## Projets & Taches

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Lister les projets actifs | *"Quels sont les projets en cours ?"* |
| Voir les taches d'un projet | *"Montre les taches du projet La Maison Du Caroubier"* |
| Creer une tache | *"Cree une tache : Livrer plans etage 2, projet Villa M, assignee a Amira"* |
| Modifier le statut d'une tache | *"Marque la tache Fondations comme terminee"* |
| Voir les jalons d'un projet | *"Quels sont les jalons du projet Villa M ?"* |
| Chercher les taches en retard | *"Quelles taches ont depasse leur date limite ?"* |

---

## Feuilles de temps

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Voir les heures saisies | *"Combien d'heures ont ete saisies cette semaine ?"* |
| Saisir du temps | *"Ajoute 3h sur le projet Villa M, tache Plans, pour aujourd'hui"* |
| Modifier une entree | *"Corrige mon temps d'hier sur Villa M a 4h au lieu de 3h"* |
| Voir les heures par projet | *"Quel est le total d'heures sur chaque projet ce mois ?"* |

---

## RH & Employes

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Lister les employes | *"Liste tous les employes actifs"* |
| Voir les departements | *"Quels departements existent ?"* |
| Consulter les presences | *"Qui etait present hier ?"* |
| Voir les conges | *"Qui est en conge cette semaine ?"* |
| Voir les candidatures | *"Montre les candidatures en cours pour le poste architecte"* |

---

## Inventaire & Produits

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Chercher un produit | *"Trouve le produit Beton C25"* |
| Voir le stock d'un produit | *"Quelle est la quantite en stock de Ciment CPJ 42.5 ?"* |
| Creer un produit | *"Cree un produit : Acier HA 12, unite kg, prix 250 DA"* |
| Voir les mouvements de stock | *"Montre les dernieres entrees en stock"* |
| Voir les entrepots | *"Quels entrepots sont configures ?"* |

---

## Achats

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Voir les commandes fournisseurs | *"Montre les commandes d'achat en cours"* |
| Voir les lignes d'un bon de commande | *"Detail du bon d'achat P00012"* |
| Creer une commande fournisseur | *"Cree un bon de commande fournisseur pour 50 sacs de ciment"* |

---

## Fabrication

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Voir les ordres de fabrication | *"Quels ordres de fabrication sont en cours ?"* |
| Consulter les nomenclatures (BOM) | *"Montre la nomenclature du produit Fenetre PVC"* |
| Voir les postes de charge | *"Quels ateliers sont configures ?"* |

---

## Assistance / Support

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Voir les tickets ouverts | *"Quels tickets de support sont en attente ?"* |
| Creer un ticket | *"Cree un ticket : Fuite toiture Villa M, priorite haute"* |
| Modifier un ticket | *"Assigne le ticket #15 a Amira"* |

---

## Site Web & Blog

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Voir les pages du site web | *"Liste les pages publiees sur le site"* |
| Voir les articles de blog | *"Quels articles de blog avons-nous ?"* |

---

## Documents & Connaissances

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Chercher un document | *"Trouve le document Plans Villa M"* |
| Voir les articles Knowledge | *"Montre les articles de la base de connaissances"* |

---

## Planning & Calendrier

| Ce que vous pouvez demander a Claude | Exemple de question |
|---|---|
| Voir les evenements a venir | *"Quels rendez-vous sont prevus cette semaine ?"* |
| Voir les types de rendez-vous | *"Quels types de creneaux de rendez-vous existent ?"* |

---

## Analyses transversales

Claude peut croiser les donnees entre modules. Exemples :

| Question transversale | Modules concernes |
|---|---|
| *"Quel client genere le plus de chiffre d'affaires ?"* | Ventes + Contacts |
| *"Combien d'heures ont ete passees sur les projets de Aicha BENZAZA ?"* | Feuilles de temps + Projets + Contacts |
| *"Quelles opportunites CRM n'ont pas de devis associe ?"* | CRM + Ventes |
| *"Quels produits ont ete achetes mais jamais vendus ?"* | Achats + Ventes + Produits |
| *"Resume l'activite du mois : ventes, factures, paiements, heures"* | Tous les modules |

---

## ATTENTION — Operations sensibles et risques

### Operations dangereuses en mode ecriture

| Risque | Description | Conseil |
|---|---|---|
| **Suppression de contacts** | Supprimer un contact supprime potentiellement l'historique lie (factures, commandes). Odoo peut bloquer si des documents sont lies, mais pas toujours. | Ne jamais demander a Claude de supprimer un contact sans verification |
| **Modification de factures** | Modifier une facture validee (posted) peut creer des incoherences comptables. | Ne modifier que les factures en brouillon |
| **Suppression de lignes de commande** | Supprimer des lignes sur une commande confirmee peut impacter la facturation et les livraisons. | Verifier le statut avant toute modification |
| **Modification de prix** | Claude peut modifier les prix unitaires sur les devis, commandes et factures sans demander de confirmation. | Toujours verifier les montants apres modification |
| **Creation de doublons** | Si on demande "cree un contact Mohamed" sans preciser, Claude peut creer un doublon d'un contact existant. | Toujours demander a Claude de chercher d'abord si le contact existe |
| **Donnees comptables** | Creer ou modifier des ecritures comptables peut fausser la comptabilite. | Reservez les ecritures comptables aux utilisateurs formes |
| **Mouvements de stock** | Creer des mouvements de stock manuellement peut desynchroniser les quantites reelles. | Preferer les circuits normaux (reception, livraison) |
| **Donnees RH** | Les informations employes (salaire, conges) sont sensibles. Claude y a acces en lecture et ecriture. | Limiter l'acces MCP aux personnes autorisees |

### Ce que Claude ne peut PAS faire (meme en mode ecriture)

| Action impossible | Raison |
|---|---|
| Confirmer / valider une commande de vente | Necessite l'appel a `action_confirm()` — non disponible via XML-RPC |
| Valider / publier une facture | Necessite `action_post()` |
| Envoyer un email depuis Odoo | Necessite une action serveur |
| Generer un PDF (devis, facture, rapport) | Necessite le moteur de rapport Odoo |
| Effectuer un rapprochement bancaire | Necessite un wizard interactif |
| Lancer un inventaire physique | Necessite un wizard |
| Signer un document (module Signature) | Necessite le workflow de signature |
| Installer ou desinstaller un module | Non accessible via XML-RPC standard |
| Modifier les droits d'acces ou les roles | Possible techniquement mais extremement dangereux |

### Bonnes pratiques

1. **Toujours verifier avant de modifier** — Demandez a Claude de vous montrer l'enregistrement avant de le modifier
2. **Pas de suppression en masse** — Ne demandez jamais "supprime tous les brouillons" ou "nettoie les doublons"
3. **Utilisez le mode lecture d'abord** (`YOLO=read`) pour explorer sans risque
4. **Un seul utilisateur MCP a la fois** — Evitez les conflits si plusieurs personnes utilisent Claude sur le meme Odoo
5. **Sauvegardez regulierement** — Avant toute operation en masse, assurez-vous d'avoir une sauvegarde recente
6. **Claude ne remplace pas Odoo** — Utilisez Claude pour rechercher, analyser et preparer des donnees. Utilisez l'interface Odoo pour valider, confirmer et envoyer.

---

*Document genere le 29 mars 2026 — Serveur MCP : mcp-server-odoo v0.5.0*
*Instance : 1161 Architects — 1161-studio-design1.odoo.com*
