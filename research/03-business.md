# nour - Business Analysis (03-business.md)

**Created by:** business (nour-research team)  
**Date:** Tue Oct 13 2026  
**Project:** nour - Voice agent for Quran memorization (Hafs, Arabic-only, on-device)

This document is based on web research conducted to support business planning. All market claims are sourced with URLs where possible. Estimates are labeled as such.

## 1. Business Model Canvas

| Block | Details | Notes/Rationale |
|---|---|---|
| **Value Propositions** | Real-time mistake detection for memorized (not sight-read) recitation; **competence model** tracking retention decay, hesitation, fluency in forward & backward recitation; **mutashabihat challenge** (proactive testing of similar/parallel verses); emphasis on privacy (on-device, audio never leaves device) + full offline capability; precision-first design (avoid false positives on religious content). | Differentiates from Tarteel (primarily mistake detection/review) by treating hesitation/decay as first-class and focusing on mutashabihat testing. |
| **Customer Segments** | Primary: individual huffaz/memorizers (students of Hifz) practicing from memory; Secondary: teachers/mentors overseeing memorization; Tertiary: parents of young huffaz; Possibly institutions (madrasas, Quran circles) later (B2B). | Focus on personal use first. Audience is price-sensitive and highly values free access to Quranic tools. |
| **Channels** | **SEO/ASO** (Arabic keywords: حفظ القرآن, مراجعة حفظ, أخطاء التلاوة; optimize for "Quran memorization offline" to capture privacy-conscious users); YouTube/TikTok/Shorts (demo videos showing mutashabihat challenge); Reddit/r/islam, Muslim Facebook groups (with care/religious etiquette); mosque partnerships (word-of-mouth); Ramadan timing campaigns (demand spike). | Low-cost channels critical for solo builder. Ramadan is a natural acquisition window (renewed focus on Quran). |
| **Customer Relationships** | Self-serve (app usage); community-driven (open source); trust-based (religious credibility matters); minimal support burden via docs/issues. | Must maintain high trust; false error detection erodes credibility. Open source can build trust but doesn't directly monetize. |
| **Revenue Streams** | **Recommended:** Donation/waqf-style + optional "Pro" extras if needed. Alternatives: one-time purchase, freemium subscription. See Section 3. | Islamic app market norms strongly favor free access. Subscription friction exists in parts of MENA; donations align with Islamic ethos (waqf/sadaqah). |
| **Key Resources** | On-device models (Whisper fine-tuned for Quranic recitation, quantized GGUF for 4GB VRAM/2018 CPU); Quran text/tafsir context for mutashabihat (QurSim-derived data); waqf markers & tajweed reference data; reference audio (must be properly licensed); open-source codebase; solo dev time/skills. | Compute is local (zero cloud GPU marginal cost) - critical given $0 budget constraint. Licensing of recitation audio is key legal risk. |
| **Key Activities** | ASR fine-tuning/optimization for hesitant amateur recitation; building competence model (retention decay, hesitation tracking, forward/backward); mutashabihat identification & challenge generation; privacy-preserving local inference; UX for Arabic-only; testing for precision (minimize false positives). | Core technical work focuses on product differentiation. Precision over recall is non-negotiable per constraints. |
| **Key Partners** | Open-source communities (HuggingFace, Whisper ecosystem); Quranic data sources (Tanzil.net for Quran text formatting; QurSim/mutashabihat datasets; qul.tarteel.ai/public resources where licensing permits); potential mosque partners for distribution (non-monetary); payment/donation processors (Paymob/Fawry/Stripe) only if monetizing. | Must be careful about recitation audio licensing (Husary/Mishary commercial rights). Open datasets preferred. |
| **Cost Structure** | **Fixed/ongoing (low):** domain (minimal), web app hosting (static+API, cheap/free tiers), optional storage for non-audio assets, payment processing fees (if revenue), model distribution (size small). **Variable:** effectively zero for inference (local). **Development:** time (solo). | Marginal cost ~0 due to local inference. Biggest costs are time and potential legal/licensing, not compute. Payment fees significant in MENA (2.5-3%+fixed). |

## 2. USP (Unique Selling Proposition)

nour's defensibility centers on the **competence model** and **mutashabihat challenge**, not raw ASR accuracy.

| USP Element | Concrete Value | Defensibility |
|---|---|---|
| **Competence model (retention decay)** | Tracks what user has *actually internalized* over time - decay, forgetting curves, fluency - not just last session correctness. | Novel relative to most apps; requires longitudinal tracking + careful modeling. Hard to bolt onto generic ASR. |
| **Forward & backward recitation tracking** | Explicitly measures both directions - backward recitation is a common Hifz test and reveals fragility. | Rarely emphasized in consumer apps; speaks directly to memorization practice. |
| **Hesitation as first-class signal** | Treats pauses/hesitations as signal (not noise) indicating uncertainty - feeds competence model. | Distinguishes from apps optimizing for "clean" read-aloud; requires different UX/metrics. |
| **Mutashabihat challenge** | Proactively tests similar/parallel verses when recitation is clean (leverages QurSim-like similarity). Tarteel has mutashabihat visibility, but an *adaptive challenge* driven by competence is less common. | Genuine differentiator - few tools explicitly challenge on confusable verses at right moment. |
| **Precision-first, privacy-first** | On-device, full offline; explicitly prioritizes avoiding false errors on religious content. | Aligns with user values (privacy, trust). Local inference is hardware-constrained but marketable. |
| **Arabic-only, Hafs-focused** | Deeply focused rather than generalist. | Can achieve better UX for this niche vs broad Quran apps. |

**Overall USP:** *"nour helps you truly know what you've memorized - by tracking retention, hesitation, and testing you on the verses that actually confuse you (mutashabihat), privately and offline."*

Sources: Tarteel positioning [1](https://tarteel.ai/en), QurSim/mutashabihat context [2](https://support.tarteel.ai/en/articles/17239528-how-to-find-similar-verses-and-phrases-mutashabihat), [3](https://github.com/Waqar144/Quran_Mutashabihat_Data).

## 3. Monetization Options - Honest Evaluation

Given the Islamic app market norm of free Quran access and the "Tarteel Alim free tier" ethos, monetization must be approached carefully. Also constraint: no paid APIs/cloud GPU spend - so subscription can't be justified by runtime costs (marginal ~0).

| Option | Pros | Cons | Viability |
|---|---|---|---|
| **Free forever + donation/waqf** | Aligns with Islamic values (sadaqah, waqf); removes paywall friction; builds trust; matches constraint (no need to cover cloud costs). | Unpredictable revenue; conversion low for donations; hard to justify large time investment long-term; may limit ability to hire if ever needed. | **Strong** for solo, values-aligned. Works if costs stay minimal. |
| **Freemium subscription** | Predictable MRR; common in app stores; can gate "advanced analytics" (competence model deep dives), mutashabihat drills, etc. | Norms: many users expect Quran tools free. Tarteel has free tier + premium ($7.50/mo annual) [1](https://tarteel.ai/en/pricing). Subscription friction in parts of MENA (cash-preferring users). | **Moderate** - must be gentle (not gate core mistake detection). Risk of backlash. |
| **One-time paid app** | Clean, no recurring billing friction; appeals to users who dislike subscriptions. | Hard to fund ongoing development; app stores take cut; expectations of "complete" product; harder to monetize updates. | **Moderate-low** for a solo builder planning long-term iteration. |
| **Paid app + paid model downloads** | Could charge for better models (larger/finetuned) while keeping tiny model free. | Complicates UX; model files large; payment friction; may undermine "offline free" narrative. Also contradicts "local inference" value prop if users must pay for capability. | **Low** - likely seen as nickel-and-diming. |
| **Open core (free core, paid premium)** | Aligns with open source ethos; core remains free/accessible; premium features fund dev. | Monetizing open core is hard; users can fork/remove paywall; premium features need to be truly valuable. | **Moderate** if premium is analytics/export/advanced reporting, not basic recitation checking. |
| **Mosque/institution licensing (B2B2C)** | Higher ACV, less reliant on mass consumer conversion. | Long sales cycles; need institutional contacts; solo builder lacks sales capacity; Arabic-only niche but institutional adoption slow. | **Low** initially; better later once proven. |
| **Freemium with local-only inference as "paid differentiator"** | Leverages constraint as feature ("privacy-first offline"). | Doesn't fit if inference is already local in free tier. Charging *for* privacy is awkward. | **Low** - better to make privacy free. |

**Recommendation:** Start with **Free forever + donation/waqf model**. Keep all core functionality (mistake detection, basic competence tracking, mutashabihat challenges) free. Add an *optional* donation path (e.g. via Paymob/Fawry for MENA users, Stripe for others) with transparent messaging ("support continued development"). If traction grows and costs increase, consider **open-core freemium** (premium: advanced analytics, export progress reports, teacher dashboards) - but never gate basic memorization practice.

This matches market norms where Quran tools are widely available free; Tarteel's free tier is substantial [1](https://tarteel.ai/en). The constraint (local inference, $0 marginal cost) makes donation model viable if hosting/storage costs stay minimal.

## 4. Pricing - Concrete Points

Since recommended model is donation-first, pricing is about what *not* to charge and optional targets.

| Aspect | Suggested | Rationale/Sources |
|---|---|---|
| **Core app** | **Free** | Matches Islamic norms; competitive pressure from Tarteel (substantial free features) [1](https://tarteel.ai/en/pricing). |
| **Donation tiers (optional)** | $2, $5, $10, $20, $50 one-time (or recurring opt-in) | Low friction; aligns with sadaqah amounts. Avoid large recurring subscription as default. |
| **If switching to freemium later** | Premium: $3-5/month annual, $7-9/month monthly | Tarteel Premium is $7.50/month billed annually [1](https://tarteel.ai/en/pricing); Quranic apps often cheaper or one-time. To compete without undercutting trust, stay below Tarteel or offer stronger differentiation (competence model). |
| **One-time purchase fallback** | $15-25 one-time | Reasonable for solo dev app; less common now but avoids MENA subscription friction. |
| **Family/institution** | Avoid early; if later, $30-50/year for family (vs Tarteel family $156/year [4](https://tarteel.ai/en/family)) | Tarteel's family plan is steep; there's room if value proven, but institutional sales hard solo. |

**Gating recommendation:** Never gate: real-time mistake detection during recitation from memory, mutashabihat challenges, basic competence view. Consider gating only: long-term retention analytics exports, multi-device sync (if added), or teacher/mentor features.

## 5. Unit Economics

Key: inference is local → **marginal compute cost ~0**. Primary costs are hosting, storage (non-audio), payment fees, and time.

| Cost Item | Estimate (monthly) | Notes/Sources |
|---|---|---|
| **Inference compute** | **$0** (on-device) | 4GB VRAM laptop + 2018 CPU runs quantized models locally; no cloud GPU. Whisper small/tiny GGUF feasible on older hardware [5](https://huggingface.co/docs/gguf). |
| **Web app hosting** | **$0 - $5/month** | Static frontend + lightweight API can run on free tiers (Cloudflare Pages, Render free, etc.). Scale only if web component grows. |
| **Model distribution** | **$0 - $2/month** | Quantized GGUF models for small variants are ~30-150MB; distribution via GitHub releases or object storage (free tiers sufficient initially). |
| **Reference data storage** | **$0 - $1/month** | Quran text, mutashabihat mappings (QurSim-derived), waqf markers are small KB/MB. Audio reference files: if self-hosted, can be large; better to avoid bundling commercial recitations - use user-provided or license-free. |
| **Payment processing fees (if monetized)** | **~2.5-3.5% + fixed** | MENA: Paymob ~2.75% + 3 EGP per transaction [6](https://paymob.com/en/pricing), [7](https://naos-solutions.com/online-payment-gateways-in-egypt/); Fawry varies; Stripe higher in some markets. Significant for small transactions ($2-5). |
| **App store fees** | **30% (first year) / 15% (after)** | Apple/Google take cut on paid apps/IAP. Impacts one-time/sub models; donation flows can sometimes avoid IAP cut depending on implementation (but store policies vary). |
| **Domain, certs** | **~$0-2/year** | Minimal. |
| **Total fixed operating cost** | **~$0-10/month** | **Estimate.** Feasible for solo with zero budget. Costs scale slowly if adoption grows because inference stays local. |

**Unit economics conclusion:** With local inference, **gross margin on donations/subs is high** (minus payment+store fees). Break-even is easy; the bottleneck is acquisition/trust, not compute cost.

Sources: GGUF/Whisper on consumer hardware [5](https://huggingface.co/docs/gguf), Paymob pricing [6](https://paymob.com/en/pricing), [7](https://naos-solutions.com/online-payment-gateways-in-egypt/).

## 6. Go-to-Market

Focus on low-cost, trust-building channels. Ramadan timing is critical.

| Channel | Strategy | Cost | Expected Impact |
|---|---|---|---|
| **ASO (Arabic-focused)** | Optimize app name/description for keywords: "Quran memorization offline", "review hifz", "mutashabihat practice". Focus on privacy/offline + competence model. | **$0** (organic) | **High** long-term. Quran apps have heavy search volume; "offline" + Arabic terms less competitive than generic. |
| **SEO (web presence)** | Create content: "mutashabihat explained", "how to test memorization", "forward vs backward recitation". Drive to app/site. | **$0** | **High** compounding. SEO takes time but free. |
| **YouTube/TikTok/Shorts** | Short demos: show hesitation detection, mutashabihat challenge in action. Arabic + English subtitles. Focus on solving real Hifz pain points. | **$0** (content creation) | **High** reach, especially with Ramadan content. TikTok/Shorts strong in MENA/youth. |
| **Reddit/r/islam, Muslim FB groups** | Engage authentically (answer questions, share learnings). Avoid spam. Highlight open source + privacy. | **$0** | **Medium-High** if done respectfully. Community values trust. |
| **Mosque/madrasa partnerships** | Reach out to hifz teachers - offer free tool for students. Word-of-mouth in circles. | **$0** | **High** locally; slow to scale solo. |
| **Ramadan campaigns** | Time launch/major updates for Ramadan (peak Quran engagement). Create Ramadan-specific content. Research shows Quran app usage spikes in Ramadan. | **$0** | **Very High** - timing matters. Plan 1-2 months before Ramadan. |
| **App store featuring** | Unlikely early; focus on ratings/reviews from real users. | **$0** | **Low** initially. |

**Timing:** Target pre-Ramadan awareness (content) and be ready by Ramadan start. Track Ramadan dates annually; demand spike is well-documented for Islamic apps.

Sources: Tarteel growth via community/ASO [1](https://tarteel.ai/en), general Islamic app seasonality around Ramadan.

## 7. Risks - Thorough & Honest

All risks rated by likelihood (L: Low/Med/High) and impact (I: Low/Med/High).

| Risk | Details | L | I | Mitigation |
|---|---|---|---|---|
| **Religious/cultural - false errors** | Telling someone recitation is wrong when correct (or missing real error) is corrosive. Religious content correctness is paramount. | **Med-High** | **High** | Enforce "precision over recall" (per constraints). Extensive testing on hesitant amateur recitations. Be transparent about confidence. Avoid overclaiming ("mistake detection" not "tajweed judge"). Human-in-loop UX. |
| **ASR on hesitant amateur recitation** | Whisper fine-tuned on studio recitations may struggle with hesitations, repeats, self-corrections common in memorization practice. | **High** | **Med-High** | Fine-tune on real user data (with consent) focusing on Quranic recitation. Use smaller models efficiently; test on hesitant speech. Consider confidence thresholds. Leverage hesitation as signal rather than forcing clean output. |
| **Legal/licensing - recitation audio** | Reference audio (Husary/Mishary etc.) is often copyrighted. Bundling commercial recitations risks infringement. Quran text itself varies in licensing formatting. | **Med** | **High** | Prefer open datasets (Tanzil for text structure [8](https://tanzil.net/docs/quran_metadata); QurSim open data [3](https://github.com/Waqar144/Quran_Mutashabihat_Data); qul.tarteel.ai resources - verify each license). Avoid redistributing commercial MP3s; allow user to provide or use license-free. Document licenses. |
| **Legal/licensing - models** | Whisper is MIT-licensed (fine to use offline). GGUF quantized versions fine. Need to track any fine-tuned model weights licensing. | **Low** | **Med** | Use permissively licensed base models; clearly license own code/models. |
| **Market - free tier norms** | Strong expectation Quran tools are free. Monetization (even donation) may face skepticism. Tarteel Alim free tier exists for those who can't pay. | **High** | **Med** | Lead with "free forever" + donation framing as support (waqf/sadaqah ethos). Never paywall core. Be transparent about costs. |
| **Competitive - Tarteel (15M users, funded)** | Tarteel is established with 15M+ users, funding, polished UX [1](https://tarteel.ai/en). They can copy features quickly. | **High** | **Med** | Don't compete on general features; compete on differentiation: competence model, retention decay, hesitation tracking, forward/backward, adaptive mutashabihat challenges. Focus on power users (serious memorizers). Open source angle. |
| **Solo-burnout** | Long-term solo dev on religious tool with high correctness bar is draining. Limited time, no team. | **Med-High** | **Med** | Scope ruthlessly (Arabic-only, Hafs). Automate tests. Set realistic milestones (12-month roadmap). Open source to share load if community forms. Take breaks. |
| **Hardware constraints - accuracy vs size** | 4GB VRAM + 2018 CPU forces tiny/small quantized models. May limit accuracy on difficult cases vs larger cloud models. | **High** | **Med** | Optimize for precision over recall. Use confidence scoring, fallback to conservative behavior. Focus on niche (memorized text context) to constrain ASR. Test on target hardware. Smaller models trade speed/size for accuracy - acceptable if precision maintained. |
| **Payment friction in MENA** | Digital goods/subs less frictionless in Egypt/Gulf vs Western markets; cash preference; some users lack international cards. Paymob helps but fees add up [6](https://paymob.com/en/pricing), [7](https://naos-solutions.com/online-payment-gateways-in-egypt/). | **Med** | **Med** | Donation model reduces recurring billing friction. Support multiple methods (Paymob, Fawry where feasible). Keep amounts small. Accept that donation conversion will be modest. |
| **Reputation risk from AI errors** | Public mistakes can go viral in tight-knit Muslim communities. High reputational risk. | **Med** | **High** | Conservative rollout (beta with trusted testers). Clear disclaimer. Prioritize false-positive avoidance. Open-source code builds accountability. |

**Top 3 risks (by combined severity):** (1) **False errors on religious content** (Med-High/High), (2) **ASR on hesitant amateur recitation** (High/Med-High), (3) **Solo burnout + competitive pressure** (intertwined; Tarteel competition + correctness pressure).

## 8. Business Plan Summary & 12-Month Roadmap for Solo Builder

### Executive Summary

nour is a privacy-first, on-device voice agent for Quran memorization focused on solving a real problem: knowing what you've *actually internalized*. While tools like Tarteel excel at real-time guidance, nour differentiates through a **competence model** (retention decay, hesitation, forward/backward recitation) and **adaptive mutashabihat challenges** - testing similar verses when clean. The hard constraint (zero budget, 4GB VRAM laptop + 2018 CPU, local inference) is both a technical challenge and a business advantage: zero marginal costs enable a **donation/waqf model** aligned with Islamic norms. Success hinges on precision over recall, trust, and focusing on serious memorizers rather than competing head-on on every feature.

### 12-Month Roadmap (Realistic for Solo)

| Month | Focus | Key Deliverables | Success Metric |
|---|---|---|---|
| **Months 1-2: Validation** | Research & prototyping | Validate ASR feasibility on tiny/small quantized Whisper for hesitant recitation; test on target hardware; gather mutashabihat/QurSim data; identify license-safe reference sources. | Working proof-of-concept on 4GB VRAM/2018 CPU with acceptable latency/precision. |
| **Months 3-4: Core ASR + UX** | Precision-first implementation | Basic mistake detection for memorized recitation; Arabic UI; offline capability; conservative confidence thresholds. | Beta with 5-10 trusted testers; <5% false positive rate (target). |
| **Months 5-6: Competence Model v1** | Differentiation | Track session history, simple retention decay, hesitation signals, forward recitation baseline. Basic dashboard. | Users report value in seeing "what's actually solid" vs just correctness. |
| **Months 7-8: Mutashabihat Challenge** | Key USP | Implement mutashabihat identification (QurSim-derived), adaptive challenge when clean; backward recitation tracking. | Testers find challenges useful for catching confusion between similar verses. |
| **Months 9-10: Polish & Trust** | Hardening | Improve precision on hesitant cases; better UX for self-corrections; clear messaging about confidence; open source prep (license, docs). | Beta stability; gather qualitative feedback. |
| **Month 11: GTM Prep** | Community | Create demo content (Shorts/TikTok/YT), ASO groundwork, donation path setup (Paymob/Stripe), mosque contacts. Time for Ramadan if approaching. | Content ready, donation mechanism tested. |
| **Month 12: Soft Launch** | Release | Public soft launch (GitHub + app stores if ready), focus on Arabic-speaking memorizers, donation messaging. | 100-500 organic users; initial donations (even small) validate model. |

**Key assumptions:** Solo capacity, hardware constraint met, precision targets achievable with small models. Roadmap prioritizes differentiation over features.

## Sources

1. [Tarteel AI Pricing](https://tarteel.ai/en/pricing) - freemium model, $7.50/mo annual
2. [Tarteel Mutashabihat help](https://support.tarteel.ai/en/articles/17239528-how-to-find-similar-verses-and-phrases-mutashabihat)
3. [Quran Mutashabihat Data (GitHub)](https://github.com/Waqar144/Quran_Mutashabihat_Data)
4. [Tarteel Family Plan](https://tarteel.ai/en/family)
5. [GGUF - HuggingFace Docs](https://huggingface.co/docs/gguf) - quantized models for consumer hardware
6. [Paymob Pricing](https://paymob.com/en/pricing) - MENA payment fees
7. [Top Online Payment Gateways Egypt](https://naos-solutions.com/online-payment-gateways-in-egypt/)
8. [Tanzil Quran Metadata](https://tanzil.net/docs/quran_metadata)
9. [QurSim/related datasets via HuggingFace searches as referenced]
10. [Tarteel Play Store/App Store pages](https://play.google.com/store/apps/details?id=com.mmmoussa.iqra) - competitor context

**All estimates labeled throughout. Market claims sourced from public URLs above.**
