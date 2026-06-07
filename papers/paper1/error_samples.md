# Paper 1 — Qualitative Error Samples (hard-core: all 5 models wrong, t=0.0)

Each item below was answered **incorrectly by all five base models** at greedy decoding — candidate cases for the Error Analysis section. `question_id` indexes `data/datasets/medqa_focused_1030.json`.


## Clinical Findings  (hard-core count: 41)

**Q16.** A 74-year-old man is brought to the emergency department after he had copious amounts of blood-stained stools. Minutes later, he turned sweaty, felt light-headed, and collapsed into his wife’s arms. Upon admission, he is found to have a blood pressure of 78/40 mm Hg, a pulse of 140/min, and oxygen saturation of 98%. His family history is relevant for both gastric and colorectal cancer. His personal history is relevant for hypertension, for which he takes amlodipine. After an initial successful resuscitation with intravenous fluids, which of the following should be the first step in approaching this case?

- Options: A) Colonoscopy; B) Nasogastric lavage; C) Upper endoscopy; D) Mesenteric angiography
- Gold: **B) Nasogastric lavage**
- Model predictions: OLMo-3…=C, OLMo-3…=C, Qwen2.5…=C, Qwen2.5…=C, Qwen2.5…=C

**Q49.** A 55-year-old female with a history of poorly controlled hyperlipidemia and obesity presents to her primary care physician for a follow-up visit. She reports that she feels well and has no complaints. She currently takes atorvastatin. Her temperature is 99°F (37.2°C), blood pressure is 135/80 mmHg, pulse is 80/min, and respirations are 16/min. Her BMI is 31 kg/m2. Her total cholesterol is 290 mg/dl, triglycerides are 120 mg/dl, and LDL cholesterol is 215 mg/dl. Her physician considers starting her on a medication that forces the liver to consume cholesterol to make more bile salts. Which of the following adverse effects is this patient at highest risk of developing following initiation of the medication?

- Options: A) Gallstones; B) Acanthosis nigricans; C) Facial flushing; D) Fat malabsorption
- Gold: **D) Fat malabsorption**
- Model predictions: OLMo-3…=A, OLMo-3…=A, Qwen2.5…=A, Qwen2.5…=A, Qwen2.5…=A

**Q50.** An investigator is studying the mechanism regulating pigment production in the skin. She has isolated a hormone produced by the anterior and intermediate lobe of the pituitary gland that stimulates neural crest-derived cells to produce pigments through the oxidation and polymerization of the amino acid tyrosine. This hormone is most likely cosecreted with a substance that acts on which of the following receptors?

- Options: A) Vasopressin receptor; B) TSH receptor; C) Mu receptor; D) Dopamine receptor
"
- Gold: **C) Mu receptor**
- Model predictions: OLMo-3…=B, OLMo-3…=A, Qwen2.5…=D, Qwen2.5…=D, Qwen2.5…=D


## Diagnosis  (hard-core count: 30)

**Q11.** A 6-month-old girl presents to an outpatient office for a routine physical. She can sit momentarily propped on her hands, babbles with consonants, and transfers objects hand to hand. The pediatrician assures the parents that their daughter has reached appropriate developmental milestones. Which additional milestone would be expected at this stage in development?

- Options: A) Engaging in pretend play; B) Separation anxiety; C) Showing an object to her parents to share her interest in that object; D) Stranger anxiety
- Gold: **D) Stranger anxiety**
- Model predictions: OLMo-3…=C, OLMo-3…=C, Qwen2.5…=C, Qwen2.5…=C, Qwen2.5…=C

**Q26.** A 71-year-old man presents to his oncologist with nausea. He recently underwent chemotherapy for pancreatic cancer and has developed severe intractable nausea over the past week. He vomits several times a day. His past medical history is notable for gout, osteoarthritis, and major depressive disorder. He takes allopurinol and sertraline. He has a 15-pack-year smoking history and drinks 1 glass of wine per day. His temperature is 98.6°F (37°C), blood pressure is 148/88 mmHg, pulse is 106/min, and respirations are 22/min. On exam, he is lethargic but able to answer questions appropriately. He has decreased skin turgor and dry mucous membranes. He is started on a medication to treat nausea. However, 3 days later he presents to the emergency room with fever, agitation, hypertonia, and clonus. What is the most likely mechanism of action of the drug this patient was prescribed?

- Options: A) 5-HT3 receptor antagonist; B) D2 receptor antagonist; C) H1 receptor antagonist; D) M1 receptor antagonist
- Gold: **A) 5-HT3 receptor antagonist**
- Model predictions: OLMo-3…=B, OLMo-3…=B, Qwen2.5…=B, Qwen2.5…=B, Qwen2.5…=B

**Q42.** A 69-year-old man presents to the emergency department with shortness of breath that has been worsening over the past month. The patient states that he has had worsening shortness of breath that has progressed to shortness of breath with simple activities and minor exertion. When he was unable to climb the stairs to his house today, he decided to come to the emergency department. The patient has a past medical history of poorly managed diabetes mellitus, hypertension, end stage renal disease, and obesity. His current medications include insulin, metformin, lisinopril, hydrochlorothiazide, and ibuprofen. The patient is notably non-compliant with his medications. An EKG and chest radiograph are normal. The patient had dialysis two days ago and attends most of his appointments. Laboratory values are ordered and are seen below:

Serum:
Na+: 135 mEq/L
K+: 4.5 mEq/L
Cl-: 100 mEq/L
HCO3-: 19 mEq/L
Urea nitrogen: 29 mg/dL
Glucose: 75 mg/dL
Creatinine: 2.5 mg/dL
Ca2+: 9.2 mg/dL
Mg2+: 1.7 mEq/L
AST: 11 U/L
ALT: 11 U/L

Leukocyte count and differential:
Leukocyte count: 4,500/mm^3
Platelet count: 150,000/mm^3
Neutrophil: 54%
Lymphocyte: 25%
Monocyte: 3%
Eosinophil: 1%
Basophil: 1%

Hemoglobin: 8.2 g/dL
Hematocrit: 22%
Mean corpuscular volume: 82 µm^3

The patient appears comfortable at rest but demonstrates notable shortness of breath when exerting himself. His temperature is 99.5°F (37.5°C), pulse is 89/min, blood pressure is 144/85 mmHg, respirations are 10/min, and oxygen saturation is 97% on room air. Pulmonary and cardiac exam are within normal limits. Which of the following is a side-effect of the long-term therapy this patient should be started on right now?

- Options: A) Hypertension; B) Hyperkalemia; C) Hypokalemia; D) Visual halos
- Gold: **A) Hypertension**
- Model predictions: OLMo-3…=C, OLMo-3…=B, Qwen2.5…=B, Qwen2.5…=B, Qwen2.5…=C


## Mechanism/Pathophysiology  (hard-core count: 22)

**Q125.** An epidemiologist is interested in studying the clinical utility of a free computerized social skills training program for children with autism. A total of 125 participants with autism (mean age: 12 years) were recruited for the study and took part in weekly social skills training sessions for 3 months. Participants were recruited from support groups in a large Northeastern US city for parents with autistic children. Parents in the support group were very eager to volunteer for the study, and over 300 children were placed on a waiting list while the study was conducted. At baseline and at the end of the 3-month period, participants were observed during a videotaped social play exercise and scored on a social interaction rating scale by their parents. Social interaction rating scores following the 3-month intervention were more than twice as high as baseline scores (p < 0.001). During exit interviews, one parent commented, ""I knew from the start that this program was going to be life-changing for my son!"" This sentiment was echoed by a number of other parents. Which of the following is the most likely explanations for the study's result?"

- Options: A) Social desirability bias; B) Observer bias; C) Sampling bias; D) Confounding bias
- Gold: **B) Observer bias**
- Model predictions: OLMo-3…=A, OLMo-3…=A, Qwen2.5…=C, Qwen2.5…=C, Qwen2.5…=C

**Q149.** A previously healthy 36-year-old man comes to the physician for a yellow discoloration of his skin and dark-colored urine for 2 weeks. He does not drink any alcohol. Physical examination shows jaundice. Abdominal and neurologic examinations show no abnormalities. Serum studies show increased levels of alanine aminotransferase (ALT) and aspartate aminotransferase (AST). A liver biopsy is performed and a photomicrograph after periodic acid-Schiff-staining is shown. Which of the following is the most likely additional finding in this patient?

- Options: A) Bullous changes of the lung bases on chest CT; B) Beading of intra- and extrahepatic bile ducts on ERCP; C) Myocardial iron deposition on cardiovascular MRI; D) Dark corneal ring on slit-lamp examination
- Gold: **A) Bullous changes of the lung bases on chest CT**
- Model predictions: OLMo-3…=B, OLMo-3…=B, Qwen2.5…=D, Qwen2.5…=D, Qwen2.5…=D

**Q156.** A 56-year-old man presents with feelings of anxiety and fatigue for the past 4 months. He says that he has also had some weight loss, as well as occasional double vision and a gritty sensation in his eyes for the last 2 months, which is worse at the end of the day. He has also noticed some painless swelling in his fingers and lower legs during the same time period. The patient denies any recent history of fevers, chills, night sweats, nausea, or vomiting. Current medications include aspirin, simvastatin, and omeprazole. Which of the following mechanisms is most likely responsible for this patient’s condition?

- Options: A) Autoantibodies resulting in tissue destruction; B) Autoantibody stimulation of a receptor; C) Excessive exogenous hormone use; D) Infiltration of tissue by neoplastic cells
- Gold: **B) Autoantibody stimulation of a receptor**
- Model predictions: OLMo-3…=A, OLMo-3…=A, Qwen2.5…=A, Qwen2.5…=A, Qwen2.5…=A


## Next Step/Workup  (hard-core count: 30)

**Q33.** A 57-year-old man comes to the physician with a 3-month history of right flank pain. Urinalysis shows 60 RBC/hpf. Renal ultrasound shows a 3 cm, well-defined mass in the upper pole of the right kidney. A photomicrograph of a section of the resected mass is shown. Which of the following is the most likely diagnosis?

- Options: A) Clear cell renal carcinoma; B) Oncocytoma; C) Nephroblastoma; D) Angiomyolipoma
- Gold: **B) Oncocytoma**
- Model predictions: OLMo-3…=A, OLMo-3…=D, Qwen2.5…=A, Qwen2.5…=A, Qwen2.5…=A

**Q37.** A 1-month-old infant is brought to the physician for a well-child examination. His mother reports that she had previously breastfed her son every 2 hours for 15 minutes but is now feeding him every 4 hours for 40 minutes. She says that the infant sweats a lot and is uncomfortable during feeds. He has 6 wet diapers and 2 stools daily. He was born at 36 weeks' gestation. He currently weighs 3500 g (7.7 lb) and is 52 cm (20.4 in) in length. He is awake and alert. His temperature is 37.1°C (98.8°F), pulse is 170/min, respirations are 55/min, and blood pressure is 80/60 mm Hg. Pulse oximetry on room air shows an oxygen saturation of 99%. Cardiopulmonary examination shows a 4/6 continuous murmur along the upper left sternal border. After confirming the diagnosis via echocardiography, which of the following is the most appropriate next step in the management of this patient?

- Options: A) Prostaglandin E1 infusion; B) Percutaneous surgery; C) Digoxin and furosemide; D) Indomethacin infusion
- Gold: **D) Indomethacin infusion**
- Model predictions: OLMo-3…=A, OLMo-3…=A, Qwen2.5…=A, Qwen2.5…=A, Qwen2.5…=A

**Q85.** A 34-year-old G3P2103 with a past medical history of preeclampsia in her last pregnancy, HIV (CD4: 441/mm^3), and diabetes mellitus presents to her obstetrician for her first postpartum visit. She delivered her third child via C-section one week ago and reports that she is healing well from the surgery. She says that breastfeeding has been going well and that her baby has nearly regained his birth weight. The patient complains that she has been more tired than expected despite her efforts to sleep whenever her baby is napping. She relies on multiple iced coffees per day and likes to eat the ice after she finishes the drink. Her diet is otherwise unchanged, and she admits that she has not been getting outside to exercise as much as usual. Her home medications include metformin and her HAART regimen of dolutegravir, abacavir, and lamivudine. Her temperature is 98.9°F (37.2°C), blood pressure is 128/83 mmHg, pulse is 85/min, and respirations are 14/min. On physical exam, she is tired-appearing with conjunctival pallor.

This patient is at risk of developing which of the following conditions?

- Options: A) Hemolytic anemia; B) Megaloblastic anemia; C) Hyperparathyroidism; D) Restless legs syndrome
- Gold: **D) Restless legs syndrome**
- Model predictions: OLMo-3…=A, OLMo-3…=B, Qwen2.5…=A, Qwen2.5…=A, Qwen2.5…=B


## Treatment/Management  (hard-core count: 21)

**Q23.** A 65-year-old man with hypertension comes to the physician for a routine health maintenance examination. Current medications include atenolol, lisinopril, and atorvastatin. His pulse is 86/min, respirations are 18/min, and blood pressure is 145/95 mm Hg. Cardiac examination is shown. Which of the following is the most likely cause of this physical examination finding?

- Options: A) Decreased compliance of the left ventricle; B) Myxomatous degeneration of the mitral valve; C) Inflammation of the pericardium; D) Dilation of the aortic root
- Gold: **A) Decreased compliance of the left ventricle**
- Model predictions: OLMo-3…=B, OLMo-3…=D, Qwen2.5…=B, Qwen2.5…=B, Qwen2.5…=B

**Q36.** A 42-year-old woman comes to the physician because of a 2-week history of joint pain and fatigue. She has a history of multiple unprovoked deep vein thromboses. Physical examination shows small bilateral knee effusions and erythematous raised patches with scaling and follicular plugging over the ears and scalp. Oral examination shows several small ulcers. Laboratory evaluation of this patient is most likely to show which of the following?

- Options: A) Positive rapid plasma reagin test; B) Positive anti-citrullinated peptide antibodies; C) Decreased activated partial thromboplastin time; D) Negative antinuclear antibodies
- Gold: **A) Positive rapid plasma reagin test**
- Model predictions: OLMo-3…=B, OLMo-3…=B, Qwen2.5…=B, Qwen2.5…=B, Qwen2.5…=B

**Q153.** A 36-year-old woman is brought to the emergency department after being involved in a motor vehicle collision. She is alert, awake, and oriented. There is no family history of serious illness and her only medication is an oral contraceptive. Her temperature is 37.3°C (99°F), pulse is 100/min, respirations are 20/min, and blood pressure is 102/80 mm Hg. Physical examination shows ecchymoses over the trunk and abdomen. A FAST scan of the abdomen is negative. An x-ray of the chest shows no fractures. A contrast-enhanced CT scan of the chest and abdomen is performed that shows a 4-cm sharply defined liver mass with a hypoattenuated central scar. Which of the following is the most appropriate next step in management?

- Options: A) Reassurance and observation; B) Biopsy of the mass; C) Discontinue the oral contraceptive; D) Percutaneous aspiration of the mass
- Gold: **A) Reassurance and observation**
- Model predictions: OLMo-3…=D, OLMo-3…=B, Qwen2.5…=B, Qwen2.5…=B, Qwen2.5…=B
