<div align="center">
  <img src="burkina_education/public/images/logo.svg" alt="Burkina Éducation" width="96" height="96">

  # Burkina Éducation

  **ERP scolaire pour les écoles du Burkina Faso** — bâti sur Frappe Framework, ERPNext et Frappe Education.

  Français en premier · XOF/FCFA · Portails élève/parent/enseignant/personnel · Hors-ligne tolérant
</div>

---

`burkina_education` n'est pas une traduction de Frappe Education : c'est une couche métier complète — gestion scolaire, pédagogie, finances, communication et vie scolaire — pensée pour le contexte burkinabè, installée *au-dessus* de Frappe/ERPNext/Education sans jamais modifier leur code source (extensions officielles uniquement : Custom Fields, Property Setters, Custom DocTypes, hooks, permissions). Le cahier des charges complet (`prompts/master.md`) et l'analyse d'architecture détaillée module par module (`docs/architecture.md`) vivent dans le dépôt de projet qui enveloppe ce bench, pas dans ce dépôt applicatif lui-même.

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Qui utilise quoi](#qui-utilise-quoi--rôles-et-responsabilités)
- [Portails](#portails--une-seule-application-web-douze-espaces)
- [Assistant de configuration](#assistant-de-configuration-de-lécole)
- [Architecture](#architecture)
- [Installation](#installation)
- [État du projet](#état-du-projet)

## Fonctionnalités

**Structure scolaire configurable** — École, Campus, Année/Trimestre académique, Niveau, Cycle, Classe/Filière : rien n'est codé en dur, chaque école définit sa propre structure (préscolaire → lycée, ou tout autre découpage).

**Élèves & tuteurs** — Profil élève complet (matricule, filiation, statut), documents, un Tuteur peut être rattaché à plusieurs élèves et réciproquement, consentement de communication par canal (SMS/WhatsApp/e-mail/portail).

**Pédagogie & évaluation** — Curriculum → Compétences → Unités d'apprentissage → Leçons ; Barème de notation configurable (note/20, coefficients, moyennes pondérées) ; classement configurable (activable/désactivable) ; verrouillage des notes après soumission (modification = action tracée et autorisée).

**Présence** — Statuts Présent/Absent/Retard/Excusé, alertes automatiques sous un seuil configurable, interfaces rapides pour l'enseignant (« Mes classes → Faire l'appel »).

**Examens** — Planification (salle, surveillant, horaire) avec détection de conflits.

**Bulletins** — « Bulletin Burkina » : format d'impression configurable avec en-tête d'école, notes, moyennes, rang, appréciations, PDF téléchargeable.

**Finances** — Réutilise directement le moteur Frais/Facturation d'Education et la comptabilité ERPNext (Fee Category → Fee Structure → Fee Schedule → Sales Invoice) ; ajoute bourses, réductions fratrie automatiques par rang, et une abstraction Mobile Money multi-fournisseur (Orange Money, Moov Money, …) avec vérification serveur obligatoire (jamais de confirmation côté navigateur).

**Communication** — Moteur de notification agnostique du canal (SMS/WhatsApp/e-mail/in-app), modèles réutilisables (absence, paiement, rappel de frais, résultat disponible, annonce), journal d'envoi complet, annonces ciblées par audience.

**Vie scolaire** — Discipline, infirmerie (données médicales strictement cloisonnées), bibliothèque (catalogue/emprunts/retards), transport (itinéraires/affectations), cantine (formules/abonnements), internat (bâtiments/chambres/lits).

**Admissions** — Candidature → Examen du dossier → Décision → Inscription : dossier candidat (classe demandée, école précédente, documents requis, entretien, examen d'entrée), décision (acceptée/rejetée/liste d'attente), frais d'inscription, puis création automatique de l'élève et de son inscription (Program Enrollment) une fois acceptée. Les élèves ne sont plus créés directement — l'admission est désormais le seul point d'entrée.

**Sécurité & auditabilité** — Permissions par rôle appliquées côté serveur (jamais uniquement côté client), permissions documentaires pour cloisonner un Tuteur à ses seuls enfants, journal des modifications sur les données sensibles (notes, paiements, statut élève).

**Multi-portails** — Un seul SPA Vue 3 + frappe-ui, douze espaces (voir plus bas), et un utilisateur cumulant plusieurs rôles voit désormais **toutes** ses sections dans une même barre latérale — plus besoin de « changer d'espace » pour retrouver l'information d'un autre rôle.

## Qui utilise quoi — rôles et responsabilités

Chaque rôle ne voit que ce qui relève de sa responsabilité (permissions appliquées côté serveur, jamais seulement dans l'interface). La colonne **Accès** indique où ce rôle travaille au quotidien.

| Rôle | Ce qu'il fait dans le système | Accès |
|---|---|---|
| **School Director** (Directeur) | Vue d'ensemble de l'école : effectifs, présence, résultats, recouvrement des frais, alertes ; supervision de la discipline ; premier arrivé sur l'Assistant de configuration. | Portail (Direction) + Desk |
| **Academic Director** (Directeur des études) | Structure académique complète, pédagogie (curriculum/compétences/leçons), discipline, bourses, annonces, réglages académiques. | Portail (Scolarité) + Desk |
| **Registrar** (Secrétaire académique) | Admissions (candidature → décision → inscription) et configuration de la structure scolaire (Campus, Cycle, Niveau, Classe) — sous-ensemble du Directeur des études. | Portail (Scolarité) |
| **Examination Coordinator** (Coordinateur des examens) | Création et planification des examens, détection des conflits de salle/surveillant. | Portail (Scolarité) |
| **Department Head** (Chef de département) | Compétences, unités d'apprentissage et leçons de son département — mêmes droits qu'un enseignant sur la pédagogie, sans les outils d'administration du Directeur des études. | Portail (Scolarité) |
| **Secretary** (Secrétariat) | Annonces et modèles de communication (SMS/WhatsApp/e-mail). | Portail (Communication) |
| **Receptionist** (Accueil) | Annuaire élèves/tuteurs en lecture seule pour orienter un appel ou un visiteur, consultation des annonces publiées. | Portail (Accueil) |
| **Accountant** (Comptable) | Factures de frais, paiements Mobile Money, bourses — aucun accès aux notes ou à la discipline. | Portail (Comptabilité) |
| **Instructor** (Enseignant) | Ses classes, appel de présence, cahier de notes, devoirs, discipline (Class Teacher), emploi du temps, messages. | Portail (Enseignant) |
| **Librarian** (Bibliothécaire) | Catalogue, adhésions, emprunts et retours. | Portail (Bibliothèque) |
| **Transport Manager** (Responsable transport) | Itinéraires, arrêts, affectations des élèves. | Portail (Transport) |
| **Canteen Manager** (Responsable cantine) | Formules de repas, abonnements. | Portail (Cantine) |
| **Boarding Manager** (Responsable internat) | Bâtiments, chambres, lits, affectations des pensionnaires. | Portail (Internat) |
| **Clinic Staff** (Infirmerie) | Visites, soins, orientation — données médicales non visibles des enseignants. | Portail (Infirmerie) |
| **Student** (Élève) | Son profil, ses notes/bulletins, sa présence, ses frais, sa bibliothèque/transport/cantine/internat, ses annonces et messages. | Portail (Élève) |
| **Guardian** (Parent/Tuteur) | Les mêmes catégories que l'élève, pour chacun de ses enfants ; un compte peut être rattaché à plusieurs élèves. | Portail (Parent) |
| **IT Administrator** | Utilisateurs, rôles, intégrations, réglages système — délibérément laissé au Bureau (Desk) : c'est un travail d'administration système, pas un besoin de portail. | Desk uniquement |
| **HR Manager** | Employés, congés, contrats — le module RH d'ERPNext est réutilisé tel quel (pas dupliqué), voir `docs/architecture.md`. | Desk uniquement |

Un utilisateur qui cumule plusieurs rôles (par ex. un Tuteur qui est aussi Secrétaire) retrouve désormais **toutes** ces sections dans la même barre latérale du portail, chacune sous son propre en-tête — l'accès à l'information d'un rôle n'exige plus de quitter celle d'un autre.

## Portails — une seule application web, douze espaces

Un SPA Vue 3 + frappe-ui unique, monté sur `/portal`, dessert :

`Élève` · `Parent` · `Enseignant` · `Direction` · `Scolarité` (Registrar/Examens/Pédagogie/Directeur des études) · `Comptabilité` · `Bibliothèque` · `Transport` · `Cantine` · `Internat` · `Infirmerie` · `Communication` · `Accueil`

Le routeur du portail attribue automatiquement le bon espace (ou la bonne combinaison d'espaces) selon les rôles Frappe de l'utilisateur connecté — aucune configuration manuelle par utilisateur n'est nécessaire. Objectif du produit : le Bureau (Desk) de Frappe reste disponible pour l'administration système et les cas non couverts, mais le travail quotidien de chaque rôle se fait entièrement depuis son portail.

- `http://votre-site/app` — Bureau (Desk), pour l'administration système.
- `http://votre-site/portal` — Portail, pour tout le reste.

## Assistant de configuration de l'école

Une nouvelle école n'a pas à créer des dizaines de fiches à la main avant d'être utilisable. L'**Assistant de configuration** (Bureau → rechercher « Assistant de configuration de l'école », ou bouton dédié sur *Burkina Education Settings*) guide le Directeur d'école à travers :

1. **École** — identité, coordonnées, logo.
2. **Année scolaire** — dates de l'année en cours.
3. **Trimestres** — génération automatique répartie sur l'année (nombre configurable).
4. **Structure scolaire** — structure standard burkinabè (préscolaire → lycée) pré-cochée, à ajuster librement.
5. **Barème de notation** — note maximale et note de passage par défaut.
6. **Utilisateurs** — invitation du personnel clé par e-mail et rôle.

Chaque étape est ré-exécutable sans risque de doublon (idempotente) : rien n'empêche d'y revenir plus tard pour corriger une étape. La configuration des frais, moyens de paiement et fournisseurs de communication (SMS/WhatsApp) reste volontairement en dehors de l'assistant — ce sont des réglages avancés déjà bien couverts par leurs propres écrans (Fee Category/Structure, Messaging Provider) et qui gagnent à être faits une fois les bases posées.

## Architecture

```
frappe
   ↓
erpnext
   ↓
education
   ↓
burkina_education   ← ce dépôt
```

Aucune modification du code source des trois couches inférieures : chaque extension utilise les mécanismes officiels de Frappe (Custom Field, Property Setter, Custom DocType, hook, permission). Détails complets, choix d'architecture et justification module par module dans `docs/architecture.md` du dépôt de projet.

## Installation

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app burkina_education $URL_OF_THIS_REPO --branch develop
bench install-app burkina_education
```

Environnement de développement complet (Docker, création de site, données de démonstration) : `docs/installation.md` du dépôt de projet.

### Contribuer

```bash
cd apps/burkina_education
pre-commit install
```

`pre-commit` est configuré avec `ruff`, `eslint`, `prettier` et `pyupgrade`.

## État du projet

- **Phases 1 à 5** (fondations, pédagogie, finances, communication, vie scolaire) : terminées. Voir le suivi détaillé dans `docs/architecture.md` du dépôt de projet.
- **Admissions** (candidature → examen du dossier → décision → inscription, `prompts/master.md` §13) : terminé. Les élèves ne sont plus créés directement — voir `docs/architecture.md` section O du dépôt de projet.
- **Phases 6 et 7** (multi-établissement à grande échelle, reporting ministériel, IA) : non démarrées, conformément à la feuille de route de `prompts/master.md`.
- École de démonstration : **École Pilote Burkina**, données idempotentes (`bench execute burkina_education.setup.demo_data.run`) — classes, élèves, tuteurs, enseignants, notes, bulletins, factures, paiement Mobile Money simulé, bourse, annonce publiée, et trois candidatures d'admission à différents stades du parcours.

---

<sub>Licence GPL-3.0 — voir [`license.txt`](license.txt).</sub>
