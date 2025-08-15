# 🚀 Guide de Déploiement EXPERTS IA sur Render

## 📋 Configuration Render Recommandée

### 🔧 Paramètres Principaux
```
Name: EXPERTS_AI_PERSO
Runtime: Python 3
Branch: main
Root Directory: (laisser vide)
Region: Virginia (US East)
```

### ⚙️ Build & Start Commands
```bash
# Build Command
pip install -r requirements.txt

# Start Command  
python render_start.py
```

### 💰 Instance Type Recommandée
- **Pour les tests** : Starter ($7/mois) - 512MB RAM
- **Pour la production** : Standard ($25/mois) - 2GB RAM ⭐ **RECOMMANDÉ**

## 🔐 Variables d'Environnement CRITIQUES

### Variables OBLIGATOIRES
Ajoutez ces variables dans la section "Environment Variables" de Render :

```bash
# === AUTHENTIFICATION ===
ANTHROPIC_API_KEY=sk-ant-api03-VOTRE_CLE_API_ANTHROPIC
APP_PASSWORD=votre_mot_de_passe_securise

# === CONFIGURATION ===
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=50
ENABLE_SECURITY_LOGGING=true
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION=30
```

### Variables OPTIONNELLES
```bash
# === DÉVELOPPEMENT ===
ENABLE_DEBUG=false
DEV_MODE=false

# === SÉCURITÉ AVANCÉE ===
DATABASE_ENCRYPTION_KEY=votre_cle_32_caracteres
```

## 🛡️ Sécurité Intégrée

### ✅ Fonctionnalités de Sécurité Activées
- 🔐 **Authentification obligatoire** avec mot de passe
- 🚫 **Protection contre brute force** (5 tentatives max)
- ⏱️ **Blocage temporaire** (30 min après échecs)
- 📊 **Logs de sécurité** automatiques
- 🔍 **Validation fichiers** stricte (signatures, tailles)
- 🛡️ **Rate limiting** (30 req/min)
- 🧹 **Sanitisation entrées** utilisateur

### 📝 Logs de Sécurité
- Fichier automatique : `security.log`
- Événements trackés : connexions, uploads, erreurs
- Niveau configurable : INFO/WARNING/ERROR

## 📁 Configuration Avancée Render

### 🗂️ Secret Files (Optionnel)
Pour une sécurité maximale, utilisez les Secret Files :
```
/etc/secrets/app_config.env
```

### 💾 Disk Storage 
```
Mount Path: /app/data
Size: 1GB (minimum pour SQLite + logs)
```

### 🔍 Health Check
```
Path: /healthz
```

## 🚦 Procédure de Déploiement

### 1. Préparation Repository
```bash
git add .
git commit -m "Sécurisation application pour production"
git push origin main
```

### 2. Configuration Render
1. **Créer le service** : New → Web Service
2. **Connecter repo** : Votre repository GitHub
3. **Configurer build** : Commands ci-dessus
4. **Ajouter variables** : Environment Variables
5. **Choisir instance** : Standard recommandé

### 3. Variables d'Environnement
**⚠️ CRITIQUE : Configurez ces variables AVANT le premier déploiement**

```bash
ANTHROPIC_API_KEY=sk-ant-api03-[VOTRE_CLE]
APP_PASSWORD=[MOT_DE_PASSE_FORT]
```

### 4. Premier Déploiement
- Cliquez **"Create Web Service"**
- Attendez le build (3-5 minutes)
- Vérifiez les logs pour erreurs
- Testez l'authentification

## 🔧 Dépannage

### ❌ Erreurs Courantes

**1. "ANTHROPIC_API_KEY non configurée"**
```
→ Solution: Ajouter la variable dans Render
→ Vérifier: Orthographe exacte de la clé
```

**2. "APP_PASSWORD non défini"**
```
→ Solution: Définir un mot de passe fort
→ Format: Minimum 8 caractères, lettres+chiffres
```

**3. "Module non trouvé"**
```
→ Solution: Vérifier requirements.txt
→ Commande: pip install -r requirements.txt
```

**4. Port binding error**
```
→ Solution: Utiliser le script render_start.py
→ Port automatique: Variable $PORT de Render
```

### 📊 Monitoring

**Vérifier le statut:**
- Dashboard Render → Service → Events
- Logs en temps réel disponibles
- Métriques CPU/RAM automatiques

**Performance:**
- Temps de réponse < 3 secondes
- Utilisation RAM < 80%
- 60+ profils experts chargés

## 🎯 Checklist Pré-Production

- [ ] Variables ANTHROPIC_API_KEY et APP_PASSWORD configurées
- [ ] Instance Standard sélectionnée (2GB RAM)
- [ ] Build & Start commands corrects
- [ ] Authentification testée
- [ ] 60+ profils experts chargés
- [ ] Logs de sécurité fonctionnels
- [ ] Upload de fichiers sécurisé testé
- [ ] Performance validée (< 3s réponse)

## 🌐 Accès à l'Application

Une fois déployée :
```
URL: https://experts-ai-perso.onrender.com
Login: Votre APP_PASSWORD
```

## 📞 Support

**En cas de problème :**
1. Vérifier les logs Render
2. Consulter `security.log` 
3. Variables d'environnement complètes
4. Redéployer si nécessaire

---

## ⭐ Points Clés de Sécurité

🔐 **Authentification forte** - Mot de passe obligatoire
🛡️ **Protection brute force** - Blocage automatique  
📊 **Monitoring complet** - Logs détaillés
🔍 **Validation stricte** - Fichiers sécurisés
⚡ **Performance optimisée** - 60+ experts IA

**EXPERTS IA est maintenant prêt pour la production !** 🚀