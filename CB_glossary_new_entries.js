// ── NEW GLOSSARY ENTRIES ──
// All terms referenced in CARBONsnaps that previously had no glossary entry.
// Paste these into the GLOSSARY_TERMS array in the shell HTML.
// Format matches existing entries; only `expert` field required (three-level system purged).

  // ── INSTRUMENTS ──

  {
    term: 'EUA',
    aliases: ['European Union Allowances','European Union Allowance','EUAs','EUA'],
    expert: 'European Union Allowance. The compliance instrument of the EU Emissions Trading System under Directive 2003/87/EC. Each EUA entitles the holder to emit one tonne of CO2 equivalent. EUAs are allocated via free allocation to covered installations and via quarterly auctions on ICE Endex (common auction platform) and EEX (Germany, Poland). The December futures contract is the primary price benchmark. EUAs are fully fungible regardless of issuance year or Member State of origin. The EU ETS cap declines annually per the Linear Reduction Factor; from 2024–2027 the LRF is 4.3%, rising to 4.4% from 2028.',
  },
  {
    term: 'RGGI',
    aliases: ['Regional Greenhouse Gas Initiative','RGGI'],
    expert: 'Regional Greenhouse Gas Initiative. A multi-state cap-and-invest programme covering CO2 emissions from electricity generation (≥25 MW) across 11 northeastern US states: Connecticut, Delaware, Maine, Maryland, Massachusetts, New Hampshire, New Jersey, New York, Rhode Island, Vermont, and Virginia. RGGI holds quarterly sealed-bid uniform-price auctions; the clearing price functions as the market benchmark. Allowances (RGAs) are issued by participating states. A Cost Containment Reserve (CCR) releases additional allowances if prices exceed a trigger; an Emissions Containment Reserve (ECR) withholds allowances below a lower trigger. Third Program Review (2025) introduced a tighter cap trajectory from 2027.',
  },
  {
    term: 'GEO',
    aliases: ['Global Emissions Offset','GEOs','GEO'],
    expert: 'Global Emissions Offset. A standardised voluntary carbon credit contract traded on the Xpansiv CBL platform. GEO contracts represent verified emissions reductions or removals from projects certified under ICROA-endorsed standards (primarily Verra VCS and Gold Standard). The GEO is nature-inclusive: any project type is eligible. The contract has become a key benchmark for the voluntary carbon market, with spot and CME futures contracts providing price discovery. GEO trades at a premium to lower-quality credits and a discount to CORSIA-eligible units in most market conditions.',
  },
  {
    term: 'N-GEO',
    aliases: ['Nature-Based Global Emissions Offset','N-GEOs','N-GEO'],
    expert: 'Nature-Based Global Emissions Offset. A Xpansiv CBL contract restricted to nature-based carbon credits — primarily REDD+, ARR, IFM, and blue carbon projects certified under Verra VCS AFOLU methodology. Distinct from the broader GEO contract by excluding engineered removal and renewable energy projects. N-GEO prices are typically at a premium to GEO given growing corporate preference for nature-based credits and biodiversity co-benefits. N-GEO futures are listed on CME. Prices are sensitive to credibility events in the REDD+ sector.',
  },

  // ── MARKETS AND SCHEMES ──

  {
    term: 'RFS',
    aliases: ['Renewable Fuel Standard','RFS'],
    expert: 'Renewable Fuel Standard. A US federal programme under the Energy Policy Act (2005) and Energy Independence and Security Act (2007), administered by the EPA under 40 CFR Part 80. Requires transportation fuel suppliers to blend specified volumes of renewable fuels annually, expressed as Renewable Volume Obligations (RVOs). Compliance is demonstrated by retiring Renewable Identification Numbers (RINs). RFS nested categories: D6 (conventional biofuel, primarily corn ethanol), D5 (advanced biofuel), D4 (biomass-based diesel), D3 (cellulosic biofuel). Annual volume targets are set via EPA rulemaking and are subject to waiver provisions.',
  },
  {
    term: 'ETS 2',
    aliases: ['EU ETS 2','ETS2'],
    expert: 'EU Emissions Trading System 2. A second, separate EU carbon market established under Directive (EU) 2023/959 (Fit for 55), covering CO2 emissions from fuel combustion in buildings, road transport, and small industry not covered by EU ETS 1. Fuel suppliers are the regulated entities. ETS 2 enters operation in 2027 (monitoring phase from 2025). A separate cap applies, targeting a 42% reduction by 2030 versus 2005. A dedicated MSR 2 will operate from 2027. A price stability mechanism triggers enhanced allowance releases if prices exceed €45/tonne. ETS 2 allowances (ETS2As) are not fungible with EU ETS Phase 1 EUAs.',
  },

  // ── REGULATORY / GOVERNMENT BODIES ──

  {
    term: 'EPA',
    aliases: ['US Environmental Protection Agency','Environmental Protection Agency','EPA'],
    expert: 'US Environmental Protection Agency. The federal agency responsible for administering the Renewable Fuel Standard (RFS), setting Renewable Volume Obligations, processing Small Refinery Exemptions, and overseeing GHG reporting under 40 CFR Part 98. The EPA does not administer a federal carbon market; US compliance carbon pricing operates at state and regional level (RGGI, California). EPA greenhouse gas endangerment finding (2009) is the legal foundation for federal GHG regulation under the Clean Air Act.',
  },
  {
    term: 'IRS',
    aliases: ['Internal Revenue Service','IRS'],
    expert: 'Internal Revenue Service. US federal tax authority responsible for administering the clean fuel and clean energy tax credits introduced under the Inflation Reduction Act (IRA), including the 45Z Clean Fuel Production Credit, 45V Clean Hydrogen Production Credit, and 45X Advanced Manufacturing Production Credit. IRS issues guidance on eligible lifecycle methodologies (GREET-based for 45Z and 45V), prevailing wage requirements, and apprenticeship standards that affect credit availability. IRS guidance timelines are a primary source of regulatory risk for producers seeking to monetise IRA credits.',
  },
  {
    term: 'CalEPA',
    aliases: ['California Environmental Protection Agency','CalEPA'],
    expert: 'California Environmental Protection Agency. The state-level environmental agency of which CARB is a department. CalEPA oversees CARB\'s administration of the Cap-and-Trade programme and LCFS, as well as the Department of Toxic Substances Control and the State Water Resources Control Board. CalEPA\'s statutory mandate derives from the California Environmental Protection Act (1991) and the California Global Warming Solutions Act AB 32 (2006). Policy decisions at CalEPA level affect the regulatory framework within which CARB conducts rulemaking.',
  },
  {
    term: 'ICROA',
    aliases: ['International Carbon Reduction and Offsetting Accreditation','ICROA'],
    expert: 'International Carbon Reduction and Offsetting Accreditation. An accreditation body that endorses voluntary carbon standards meeting its Code of Best Practice for carbon offsetting. ICROA-endorsed programmes include Verra VCS, Gold Standard, ACR, and CAR. Endorsement signals that a standard meets minimum criteria for: additionality, permanence, independent verification, and transparency. ICROA is affiliated with IETA (International Emissions Trading Association). GEO and N-GEO contracts on CBL are restricted to credits from ICROA-endorsed programmes.',
  },

  // ── POLICY INSTRUMENTS AND MECHANISMS ──

  {
    term: 'ARP',
    aliases: ['Auction Reserve Price','ARP'],
    expert: 'Auction Reserve Price. The minimum price at which allowances can be sold in a carbon market auction, functioning as a hard price floor. In the UK ETS, the ARP was set at £22 from scheme launch and rises to £28 for the 8 April 2026 auction under the Greenhouse Gas Emissions Trading Scheme Auctioning (Amendment) Regulations 2026; from 2027 it increases annually in line with the GDP Deflator. If an auction clears below the ARP, the unsold allowances are withheld. The California CCA equivalent is the Auction Reserve Price (~$19.75 in 2024), which increases 5% plus CPI annually. The ARP prevents allowance prices from collapsing to near-zero during demand shocks.',
  },
  {
    term: 'CCR',
    aliases: ['California Code of Regulations','CCR'],
    expert: 'California Code of Regulations. The codified body of California state administrative law. The Cap-and-Trade programme regulations are found in CCR Title 17, Subchapter 10 Climate Change, Article 5, Sections 95800–96023. The LCFS regulations are in CCR Title 17, Sections 95480–95503. References to "CCR Title 17" in carbon market contexts invariably mean these climate-related instruments. CARB\'s rulemaking process for amendments must comply with the California Administrative Procedure Act and, for major rulemakings, the California Environmental Quality Act (CEQA).',
  },
  {
    term: 'TNAC',
    aliases: ['Total Number of Allowances in Circulation','TNAC'],
    expert: 'Total Number of Allowances in Circulation. The key supply metric driving the EU ETS Market Stability Reserve (MSR). Calculated annually by the European Commission as: allowances issued cumulatively − cumulative verified emissions − allowances in the MSR − allowances cancelled. When TNAC exceeds 833 million, 24% of TNAC is withdrawn into the MSR. When TNAC falls below 400 million, 100 million allowances are released from the MSR. The MSR cancellation mechanism permanently cancels allowances in the reserve exceeding the previous year\'s auction volume, creating a structural ratchet. TNAC data is published each May and is the primary forward-looking supply signal for EUA pricing.',
  },
  {
    term: 'LRF',
    aliases: ['Linear Reduction Factor','LRF'],
    expert: 'Linear Reduction Factor. The annual percentage by which the EU ETS cap declines, ensuring long-run allowance scarcity. Set at 1.74% for Phase 1–2, increased to 2.2% for Phase 3 (2013–2020) and 4.3% for 2024–2027 under the Fit for 55 revision, rising to 4.4% from 2028. The LRF applies to the total cap including free allocation and auction volumes. The rate of cap decline is the primary long-run determinant of EUA scarcity and price trajectory. Discussions on post-2030 ETS design centre on whether the LRF should be further increased or replaced with a fixed reduction pathway aligned to the 2040 climate target.',
  },
  {
    term: 'SRE',
    aliases: ['Small Refinery Exemption','SREs','SRE'],
    expert: 'Small Refinery Exemption. A provision under the US Renewable Fuel Standard (40 CFR §80.1441) allowing small refineries (≤75,000 barrels/day crude capacity) to petition the EPA for a waiver of their Renewable Volume Obligation on grounds of disproportionate economic hardship. SREs have been a persistent source of demand uncertainty in the RIN market: widespread SRE grants in 2017–2019 are estimated to have reduced D6 RIN demand by billions of gallons, materially suppressing prices. EPA SRE adjudication practices under successive administrations have been a significant policy risk variable for RIN holders and biofuel producers.',
  },
  {
    term: 'RVO',
    aliases: ['Renewable Volume Obligation','RVOs','RVO'],
    expert: 'Renewable Volume Obligation. The quantity of renewable fuel (expressed in RIN equivalents) that an obligated party under the US RFS must demonstrate compliance for in a given year. RVOs are set by EPA rulemaking, typically in Q4 of the preceding year. Obligated parties are refiners and importers of gasoline and diesel. RVO calculation: total petroleum fuel volume × nested percentage standards. Compliance is achieved by retiring RINs equal to the RVO. Carry-forward provisions allow a 20% deficit carryover to the following year. Annual RVO levels are the primary demand driver for RIN prices.',
  },
  {
    term: 'BTC',
    aliases: ['Biodiesel Tax Credit','BTC'],
    expert: 'Biodiesel Tax Credit. A US federal blender\'s tax credit of $1.00/gallon for biodiesel and renewable diesel, historically administered under IRC Section 40A. One of the most significant demand supports for US biodiesel and renewable diesel production. The BTC was replaced for taxable years from 2025 by the 45Z Clean Fuel Production Credit under the IRA. The transition from BTC to 45Z changed the credit recipient from blenders to producers, altered the credit value calculation (now lifecycle CI-based rather than flat per-gallon), and introduced prevailing wage requirements. The BTC/45Z transition has materially affected feedstock economics and supply chain incentives for renewable diesel.',
  },
  {
    term: 'SAF',
    aliases: ['Sustainable Aviation Fuel','SAF'],
    expert: 'Sustainable Aviation Fuel. Aviation fuel produced from non-fossil feedstocks — including waste oils, agricultural residues, municipal solid waste, and (prospectively) power-to-liquid synthesis — with a lower lifecycle carbon intensity than conventional Jet-A. SAF is central to aviation decarbonisation given the absence of near-term zero-emission aircraft technology for long-haul routes. Under the US 45Z credit, SAF earns a minimum $1.25/gallon credit (compared to $0.20/gal for non-aviation fuels), scaling up with CI reduction. EU ReFuelEU Aviation mandates SAF blending from 2025 (2%) rising to 70% by 2050. CORSIA accepts SAF as an alternative compliance pathway, providing a reduction in offsetting obligations proportional to the CI of the SAF used.',
  },

  // ── CARBON STANDARDS AND REGISTRIES ──

  {
    term: 'Verra VCS',
    aliases: ['Verified Carbon Standard','Verra VCS','VCS'],
    expert: 'Verified Carbon Standard. The world\'s largest voluntary carbon crediting programme by issuance, administered by Verra (formerly Verified Carbon Standard Association). Issues Verified Carbon Units (VCUs), each representing one tonne of CO2e reduced or removed. Covers a wide range of project types via approved methodologies: REDD+, ARR, IFM, renewable energy, methane destruction, and industrial processes. AFOLU (land use) projects must contribute to a pooled buffer account to address permanence risk. VCS is the primary source of GEO and N-GEO contracts on CBL. Subject to significant reputational scrutiny following 2023 investigative analysis of REDD+ methodology accuracy.',
  },
  {
    term: 'Gold Standard',
    aliases: ['Gold Standard'],
    expert: 'Gold Standard for the Global Goals. A voluntary carbon and sustainable development standard founded in 2003 by WWF and other NGOs, headquartered in Geneva. Issues Gold Standard Verified Emission Reductions (GS-VERs). Historically focused on renewable energy and cookstove projects in developing countries; scope has expanded to include land use, water, and biodiversity. Known for stronger additionality requirements and mandatory co-benefit reporting (Sustainable Development Goals indicators) relative to Verra VCS. GS-VERs are ICROA-endorsed and CORSIA-eligible. Typically commands a price premium over equivalent VCS credits due to perceived higher quality standards.',
  },
  {
    term: 'ACR',
    aliases: ['American Carbon Registry','ACR'],
    expert: 'American Carbon Registry. A US voluntary carbon standard and registry, originally established in 1996 as the GHG Registry, now operated by Winrock International. Issues ACR Emission Reductions (ACR-ERs) and Removal Units, each representing one tonne of CO2e. ACR-approved methodologies cover forestry, agriculture, coal mine methane, landfill gas, and ozone-depleting substance destruction. ACR is one of the four CORSIA-approved offset programmes (alongside Verra VCS, Gold Standard, and CAR) for Phase 1 (2024–2026). ACR enforces a minimum 100-year durability standard for geological carbon storage. ACR-ERs are ICROA-endorsed.',
  },
  {
    term: 'CAR',
    aliases: ['Climate Action Reserve','CAR'],
    expert: 'Climate Action Reserve. A US voluntary carbon offset programme established in 2008 by the California Climate Action Registry. Issues Climate Reserve Tonnes (CRTs), each representing one tonne of CO2e. CAR protocols focus on North American land use (forestry, grasslands, urban trees), livestock methane, and ozone-depleting substances. CRTs are ICROA-endorsed and approved under CORSIA for Phase 1. CAR protocols are frequently adopted as the basis for offset provisions within US compliance markets, including the California Cap-and-Trade programme (offset use capped at 4–6% of compliance obligation). CAR is distinct from CARB, though the two interact closely in the California policy ecosystem.',
  },
  {
    term: 'Article 6',
    aliases: ['Article 6'],
    expert: 'Article 6 of the Paris Agreement. The provisions governing international carbon market cooperation between countries. Three main mechanisms: Article 6.2 (bilateral cooperative approaches, enabling country-to-country transfers of Internationally Transferred Mitigation Outcomes, ITMOs); Article 6.4 (a centralised UN-supervised crediting mechanism, the successor to the Clean Development Mechanism); and Article 6.8 (non-market approaches). Full operationalisation has been repeatedly delayed across COP sessions. Article 6.4 rules were partially agreed at COP29 (Baku, 2024); the methodology approval process and corresponding adjustment requirements remain contested. Article 6 implementation is a key demand driver for high-quality voluntary carbon credits and a potential structural shift for the VCM.',
  },
  {
    term: 'Article 6.4',
    aliases: ['Article 6.4'],
    expert: 'The centralised crediting mechanism under the Paris Agreement, supervised by the Article 6.4 Supervisory Body under the UNFCCC. Issues Emission Reduction units (A6.4ERs). Intended as the multilateral successor to the Kyoto Protocol\'s Clean Development Mechanism (CDM). Key features: host country authorisation required; corresponding adjustments mandatory (host country NDC is adjusted upward when A6.4ERs are transferred internationally, preventing double-counting); methodologies approved by the Supervisory Body; independent third-party validation and verification. A6.4ERs that are not internationally transferred (used for domestic purposes) are designated as "mitigation contributions" rather than "authorised" units. Full operationalisation timeline remains uncertain as of early 2026.',
  },
  {
    term: 'A6.4ERs',
    aliases: ['A6.4ERs','Article 6.4 Emission Reductions'],
    expert: 'Article 6.4 Emission Reductions. Credits issued under the Paris Agreement Article 6.4 mechanism, supervised by the UNFCCC Article 6.4 Supervisory Body. Each A6.4ER represents one tonne of CO2e reduced or removed. Distinct from voluntary market credits (VCUs, GS-VERs) in that they require host country authorisation and mandatory corresponding adjustments. A6.4ERs authorised for international transfer can be used for CORSIA compliance and potentially by sovereign buyers toward NDC achievement. The interaction between A6.4ERs and the voluntary carbon market (particularly CORSIA) is an active area of policy development; A6.4ERs may displace some voluntary standard credits as the preferred compliance unit.',
  },
  {
    term: 'ITMOs',
    aliases: ['Internationally Transferred Mitigation Outcomes','ITMOs','ITMO'],
    expert: 'Internationally Transferred Mitigation Outcomes. The unit of account for bilateral carbon market cooperation under Article 6.2 of the Paris Agreement. ITMOs are transferred between countries under cooperative approaches, each representing one tonne of CO2e. The transferring country must apply a corresponding adjustment (increasing its NDC accounting by the quantity transferred); the receiving country records the mitigation. ITMOs are not a standardised tradeable instrument — they are accounting entries in national registries. However, ITMO-backed credits are emerging as a premium product in the voluntary market, as buyers can claim the mitigation is not double-counted in any national inventory. Singapore, South Korea, and Switzerland are among the most active ITMO framework developers.',
  },
  {
    term: 'EEU',
    aliases: ['Eligible Emissions Unit','Eligible Emissions Units','EEUs','EEU'],
    expert: 'Eligible Emissions Unit. The generic term used under ICAO\'s CORSIA programme for carbon credits that meet CORSIA Sustainability Criteria and are therefore eligible for airline offsetting compliance. EEUs must come from programmes approved by the ICAO Council; approved programmes for Phase 1 (2024–2026) include Verra VCS, Gold Standard, ACR, CAR, and others. EEUs must have vintages from 2016 onwards for Phase 1. Not all credits from approved programmes are automatically EEUs — project-level eligibility and vintage requirements apply. EEU prices trade at a premium to non-CORSIA-eligible credits from the same standard, given the additional demand from mandatory airline compliance.',
  },

  // ── PROJECT TYPE ACRONYMS ──

  {
    term: 'REDD+',
    aliases: ['REDD+'],
    expert: 'Reducing Emissions from Deforestation and Forest Degradation. A UN framework (UNFCCC) providing results-based payments to developing countries for verifiable reductions in deforestation and forest degradation, plus conservation, sustainable management, and enhancement of forest carbon stocks (the "+" elements). In voluntary carbon markets, REDD+ refers to project-level credits issued under standards like Verra VCS using AFOLU methodologies (primarily VM0007, VM0015). REDD+ is the largest single category of voluntary carbon credit issuance by volume. Faced significant credibility scrutiny in 2023 following academic and journalistic analysis suggesting overcrediting in some jurisdictions. REDD+ projects require a permanence buffer account contribution under Verra VCS.',
  },
  {
    term: 'ARR',
    aliases: ['Afforestation, Reforestation and Revegetation','ARR'],
    expert: 'Afforestation, Reforestation and Revegetation. A project category under Verra VCS (and other voluntary standards) covering the establishment of forests on land that was previously non-forest (afforestation), the re-establishment of forests on degraded or deforested land (reforestation), and the re-establishment of vegetation in degraded ecosystems (revegetation). ARR projects generate removal credits rather than avoidance credits, and are generally considered higher quality than avoided-deforestation REDD+ credits due to the direct measurability of carbon sequestration. ARR credits carry permanence risk (fire, drought, pests) addressed via buffer pool contributions. Increasingly favoured by corporate buyers seeking removal-based claims.',
  },
  {
    term: 'IFM',
    aliases: ['Improved Forest Management','IFM'],
    expert: 'Improved Forest Management. A Verra VCS project category (primarily VM0012) covering modifications to forest management practices on privately or publicly owned commercial timberland to increase carbon storage relative to a business-as-usual baseline. IFM generates avoidance credits (avoided harvesting) or enhancement credits (delayed rotation, reduced-impact logging). IFM projects in the US Pacific Northwest and Southeast have been among the highest-volume VCM project types. Additionality is a frequent criticism: demonstrating that the improved management would not have occurred without carbon finance is methodologically challenging when project owners already had economic incentives for conservation.',
  },
  {
    term: 'NBS',
    aliases: ['Nature-Based Solutions','NBS'],
    expert: 'Nature-Based Solutions. An umbrella term for carbon projects that use or restore natural ecosystems to sequester carbon or avoid emissions — encompassing REDD+, ARR, IFM, blue carbon (mangroves, seagrass, saltmarsh), and soil carbon projects. NBS credits dominate voluntary carbon market issuance by volume. They face heightened scrutiny on additionality (would the ecosystem have been conserved anyway?), permanence (natural reversal risk), and measurement uncertainty (particularly for soil carbon). Institutional buyers increasingly require NBS credits to carry robust co-benefit certifications (biodiversity, community). The N-GEO contract on CBL is restricted to NBS project types.',
  },
  {
    term: 'AFOLU',
    aliases: ['Agriculture, Forestry and Other Land Use','AFOLU'],
    expert: 'Agriculture, Forestry and Other Land Use. The Verra VCS sectoral scope covering land-based carbon projects. AFOLU methodologies govern REDD+, ARR, IFM, improved agricultural land management (IALM), avoided conversion of grasslands, and wetland restoration (including blue carbon). AFOLU projects must contribute to a pooled AFOLU buffer pool to address non-permanence risk, with contribution rates determined by a risk assessment tool. AFOLU is the largest category of VCU issuance and the primary source of credits for GEO and N-GEO contracts. The AFOLU buffer pool is subject to periodic recalculation as verified reversals occur.',
  },
  {
    term: 'BECCS',
    aliases: ['Bioenergy with Carbon Capture and Storage','BECCS'],
    expert: 'Bioenergy with Carbon Capture and Storage. A carbon dioxide removal (CDR) technology combining the combustion or processing of biomass (which absorbs CO2 during growth) with the capture and geological storage of the resulting CO2 stream. Net negative: the biogenic carbon cycle absorption plus geological storage produces a net atmospheric removal. BECCS is a major component of IPCC scenario pathways that limit warming to 1.5°C, but faces significant land use, water, and biomass sustainability constraints at scale. In carbon markets, BECCS credits are considered permanently stored and thus exempt from impermanence discount applied to biological stores. Commercial BECCS projects are at early deployment stage; the UK Drax biomass facility is among the most advanced.',
  },
  {
    term: 'DAC',
    aliases: ['Direct Air Capture','DAC'],
    expert: 'Direct Air Capture. A mechanical CDR technology that uses chemical processes to extract CO2 directly from ambient air, followed by compression and geological storage (DACCS) or utilisation. Unlike BECCS, DAC has no land use dependency and is location-flexible, but is highly energy-intensive and currently expensive ($400–1,000+ per tonne of CO2 captured). DAC credits are considered among the highest-quality voluntary carbon credits due to measurability, permanence, and lack of reversibility risk. US 45Q tax credit (up to $180/tonne for DAC with geological storage) and IRA provisions have catalysed investment in US DAC projects (Occidental 1PointFive, Climeworks). DAC is expected to play a significant role in net-zero pathways as a last-resort removal technology for residual emissions.',
  },

  // ── INTEGRITY / TARGET FRAMEWORKS ──

  {
    term: 'SBTi',
    aliases: ['Science Based Targets initiative','SBTi'],
    expert: 'Science Based Targets initiative. A non-profit body that sets and validates corporate emissions reduction targets aligned with the Paris Agreement. The SBTi Corporate Net-Zero Standard (2021) requires companies to achieve a minimum 90–95% absolute emissions reduction by 2050 versus a base year, with residual emissions addressed by permanent carbon removals — not avoidance credits. Near-term targets (5–10 year) must cover at least 95% of Scope 1 and 2 emissions and 67% of Scope 3. Targets are validated by SBTi staff against established criteria. SBTi validation is increasingly required by investors and procurement frameworks. Over 7,000 companies had committed or set SBTi targets as of 2025. SBTi does not endorse the use of carbon credits for near-term target compliance.',
  },
  {
    term: 'VCMI',
    aliases: ['Voluntary Carbon Markets Integrity Initiative','VCMI'],
    expert: 'Voluntary Carbon Markets Integrity Initiative. An initiative establishing standards for credible corporate use of voluntary carbon credits. The VCMI Claims Code of Practice (2023) defines three claim tiers for companies that use carbon credits beyond their SBTi-aligned reduction pathway: Silver (credits ≥ 20% of residual emissions, high-integrity only), Gold (credits ≥ 50%), Platinum (credits ≥ 100%). VCMI requires that credits are used in addition to, not instead of, science-based emissions reductions. Works alongside the Integrity Council for the Voluntary Carbon Market (ICVCM), which sets quality standards for credit supply. VCMI and ICVCM form the demand-side and supply-side integrity architecture for the voluntary market.',
  },
  {
    term: 'NDC',
    aliases: ['Nationally Determined Contribution','Nationally Determined Contributions','NDCs','NDC'],
    expert: 'Nationally Determined Contribution. A country\'s self-defined climate commitment under the Paris Agreement, submitted to the UNFCCC. NDCs specify emissions reduction targets, typically expressed as percentage reductions versus a base year or BAU trajectory, and may include sectoral policies and adaptation measures. NDCs are updated every five years (Global Stocktake mechanism); the current round (NDC 3.0, due 2025) was expected to represent a significant uplift in ambition ahead of COP30. Article 6 carbon market transactions are directly linked to NDCs: corresponding adjustments ensure that ITMOs transferred internationally are reflected in the host country\'s NDC accounting, preventing double-counting. Ambitious NDC targets increase pressure on domestic carbon pricing and ETS stringency.',
  },

  // ── LIFECYCLE / CARBON INTENSITY METHODOLOGY ──

  {
    term: 'CA-GREET',
    aliases: ['CA-GREET'],
    expert: 'California Greenhouse gases, Regulated Emissions, and Energy use in Transportation. A lifecycle analysis model developed and maintained by CARB for use in the California LCFS. CA-GREET 3.0 is the current version (2019–), assessing carbon intensity of fuels on a well-to-wheel basis for transport applications, including indirect land-use change (iLUC) for crop-based feedstocks. A shift to CA-GREET 4.0 is underway for new pathway applications under the July 2025 LCFS amendments. CA-GREET CI values determine whether a fuel pathway generates credits or deficits under the LCFS. Distinct from the federal GREET model (Argonne National Laboratory) used for 45Z, though both derive from the same methodological lineage.',
  },
  {
    term: 'GREET',
    aliases: ['GREET'],
    expert: 'Greenhouse gases, Regulated Emissions, and Energy use in Technologies. A lifecycle analysis model developed by Argonne National Laboratory for the US Department of Energy. GREET is the approved methodology for calculating the carbon intensity of fuels under the federal 45Z Clean Fuel Production Credit and 45V Clean Hydrogen Production Credit. GREET calculates CI on a well-to-wheel basis for transport fuels and well-to-gate for hydrogen. Treasury guidance on 45Z references GREET as the default lifecycle model pending finalisation of SAF-specific methodology. GREET is updated periodically; updates can change the CI scores of established pathways and thus the credit values available to producers.',
  },
  {
    term: 'WTW',
    aliases: ['well-to-wheel','well-to-wake','WTW'],
    expert: 'Well-to-Wheel. A lifecycle assessment boundary for transport fuel carbon intensity, covering emissions from primary resource extraction (the "well") through to energy use in the vehicle drivetrain (the "wheel"). Includes upstream extraction and processing, fuel production, distribution, and combustion. For aviation, the equivalent term is well-to-wake, extending to in-flight combustion and non-CO2 effects. WTW assessment is the standard methodology for LCFS (CA-GREET), 45Z (GREET), and CORSIA SAF certification. Distinguished from tank-to-wheel (TTW), which covers only combustion-stage emissions, and well-to-gate (WTG), which stops at the point of fuel production. WTW scope is critical: some fuels with low TTW emissions (e.g. grid electricity, grey hydrogen) have high WTW CI depending on upstream energy source.',
  },
  {
    term: 'iLUC',
    aliases: ['indirect land-use change','iLUC'],
    expert: 'Indirect Land-Use Change. The additional CO2 emissions that occur when cropland is diverted to biofuel feedstock production, causing food production to shift elsewhere, potentially triggering deforestation or conversion of carbon-rich land. iLUC is not a direct emission from the fuel supply chain but a market-mediated effect: higher demand for crop-based biofuel → higher crop prices → expansion of agricultural land in third countries. The inclusion of iLUC in lifecycle carbon intensity calculations significantly affects the competitiveness of crop-based fuels (corn ethanol, soy biodiesel, palm oil) under the California LCFS (CA-GREET includes iLUC factors). iLUC factors are modelled outputs from economic equilibrium models and are inherently uncertain; this uncertainty is a perennial source of policy debate. Waste-based and cellulosic feedstocks generally attract zero iLUC penalty.',
  },

  // ── UNITS AND MEASUREMENT ──

  {
    term: 'GWP',
    aliases: ['Global Warming Potential','GWP','GWP100'],
    expert: 'Global Warming Potential. A metric expressing the warming effect of a greenhouse gas relative to CO2 over a specified time horizon, used to convert non-CO2 emissions into CO2-equivalent (CO2e) values. GWP100 (100-year time horizon) is the standard for carbon market accounting. Key GWP100 values vary by IPCC assessment report: for methane (CH4), GWP100 = 25 (AR4, used by EU ETS), 28–34 (AR5), 27.9 (AR6). The EU ETS uses AR4 GWP values under the EU MRR. Some voluntary standards have updated to AR5 or AR6, creating a divergence in CH4-intensive project accounting. The choice of GWP timeframe (20-year GWP20 vs. GWP100) is particularly consequential for methane: GWP20 for CH4 is approximately 80, versus 28 under GWP100, significantly affecting the value of methane destruction projects. Non-CO2 aviation effects (contrails, NOx) are not yet captured by standard GWP metrics in compliance market obligations.',
  },

  // ── CALIFORNIA LEGISLATION ──

  {
    term: 'AB 32',
    aliases: ['AB 32','Assembly Bill 32'],
    expert: 'California Assembly Bill 32, the California Global Warming Solutions Act of 2006. The foundational legislation establishing California\'s GHG emission reduction mandate: return to 1990 emission levels by 2020. Directed CARB to develop and implement regulations to achieve the target, including the Cap-and-Trade programme. AB 32 was extended and strengthened by SB 32 (2016), which set a target of 40% below 1990 levels by 2030. The statutory basis for CARB\'s authority to operate the Cap-and-Trade programme and LCFS. AB 32 established California as the first US state with a comprehensive GHG emissions cap, and its architecture has influenced carbon market design globally.',
  },
  {
    term: 'SB 32',
    aliases: ['SB 32','Senate Bill 32'],
    expert: 'California Senate Bill 32, the California Global Warming Solutions Act of 2016. Extended and significantly tightened the climate mandate of AB 32: requires California to reduce GHG emissions to at least 40% below 1990 levels by 2030. Directed CARB to update its Scoping Plan and ratchet the Cap-and-Trade cap and LCFS CI targets accordingly. SB 32 is the legislative basis for CARB\'s 2022 Scoping Plan and the July 2025 LCFS amendments, which tightened CI benchmarks to align with the 2030 target. The stringency of SB 32 compliance requirements is the primary driver of CCA and LCFS price trajectory through 2030.',
  },

  // ── FINANCIAL / MARKET TERMS ──

  {
    term: 'Free allocation',
    aliases: ['free allocation','free allowance allocation'],
    expert: 'The distribution of emissions allowances to covered installations at no cost, as an alternative or supplement to auctioning. Used in the EU ETS and UK ETS to address carbon leakage risk and competitiveness concerns for trade-exposed industries. In the EU ETS, free allocation for Phase 4 (2021–2030) is calculated using product benchmarks (tonnes of allowance per tonne of output). Free allocation for CBAM-covered sectors is being phased out 2026–2034 in parallel with CBAM implementation. Free allocation creates a windfall when allowances are passed through to product prices (power sector); benchmarking aims to incentivise decarbonisation by rewarding efficient installations. UK ETS free allocation for the second period has been delayed from 2026 to 2027.',
  },
  {
    term: 'Basis risk',
    aliases: ['basis risk'],
    expert: 'The risk arising from imperfect price correlation between two related instruments or markets. In carbon markets, basis risk most commonly refers to: (1) the price divergence between EUA and UKA, which trade as structurally similar but legally separate instruments with different supply-demand dynamics, MSR parameters, and policy uncertainties — a linked ETS would collapse this basis; (2) divergence between a futures contract used for hedging and the spot or auction price at which compliance obligations are settled; (3) divergence between carbon credit types used interchangeably for compliance (e.g. EEUs from different approved programmes under CORSIA). Basis risk is material for any entity with obligations in one market who holds positions in another.',
  },
  {
    term: 'Banking',
    aliases: ['banking','allowance banking','credit banking'],
    expert: 'The ability to carry unused allowances or credits forward from one compliance period to the next, holding them for future use. Banking is permitted in the EU ETS, UK ETS, California Cap-and-Trade, and RGGI. It allows entities to accumulate positions during periods of low prices or low emissions for use when abatement costs are high, creating a demand for current-period allowances beyond immediate compliance need. Banking is a key driver of the forward curve structure and is a mechanism by which market participants express long-term price views. Borrowing (using future-period allowances for current compliance) is generally not permitted in major ETS designs. CORSIA restricts credit vintage eligibility, limiting cross-period banking in that programme.',
  },
  {
    term: 'Price floor',
    aliases: ['price floor','carbon price floor'],
    expert: 'A minimum price level below which allowances cannot be sold, implemented via an Auction Reserve Price (ARP) or equivalent mechanism. Prevents carbon market prices from collapsing to near-zero, which would eliminate the abatement incentive. In the UK ETS, the ARP is a hard floor: auctions that fail to clear at the reserve price are withdrawn. California Cap-and-Trade has an auction reserve price (~$19.75 in 2024) that increases 5% + CPI annually. The UK Carbon Price Support (CPS), a separate tax on top of the carbon price for power generators, functioned as a de facto floor in the UK during EU ETS participation and is no longer operational post-Brexit. Price floors are more politically durable than price ceilings as they benefit government auction revenues.',
  },
  {
    term: 'Price ceiling',
    aliases: ['price ceiling','cost containment reserve'],
    expert: 'A mechanism that releases additional allowances into the market if prices exceed a specified trigger level, preventing excessive price spikes. In the UK ETS, the Cost Containment Mechanism (CCM) triggers if the average secondary futures price exceeds three times the two-year trailing average for six consecutive months; the UK ETS Authority has discretion over the quantum and timing of any release. California Cap-and-Trade operates an Allowance Price Containment Reserve (APCR) with tiered trigger prices; allowances are released if auction prices hit Tier 1 ($65.72 in 2024) or Tier 2 ($74.91) thresholds. EU ETS 2 will include a price stability mechanism releasing additional allowances if prices exceed €45/tonne. Price ceilings create upside resistance in the forward curve and limit the signal for long-horizon abatement investment.',
  },
