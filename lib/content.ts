export const navLinks = [
  { href: "#home", label: "Home" },
  { href: "#about", label: "About Us" },
  { href: "#services", label: "Services" },
  { href: "#products", label: "Products" },
  { href: "#projects", label: "Projects" },
  { href: "#gallery", label: "Gallery" },
  { href: "#contact", label: "Contact" },
] as const;

export const hero = {
  brand: "Mark Wholesale",
  headline: "Industrial Wholesale Supply For Concrete Industry",
  subhead: "Rebar & Wire Mesh Supply",
  ctaPrimary: { label: "View Products", href: "#products" },
  ctaSecondary: { label: "Contact Us", href: "#contact" },
};

export const inventoryProducts = [
  {
    name: "H-Pile",
    icon: "/media/products/mcp/h-pile.webp",
    image: "/media/products/mcp/h-pile.webp",
  },
  {
    name: "Bars",
    icon: "/media/products/mcp/bars.webp",
    image: "/media/products/mcp/bars.webp",
  },
  {
    name: "Channel",
    icon: "/media/products/mcp/channel.webp",
    image: "/media/products/mcp/channel.webp",
  },
  {
    name: "Pipe Pile",
    icon: "/media/products/mcp/pipe-pile.webp",
    image: "/media/products/mcp/pipe-pile.webp",
  },
  {
    name: "Rail Shapes",
    icon: "/media/products/mcp/rail-shapes.webp",
    image: "/media/products/mcp/rail-shapes.webp",
  },
  {
    name: "Plate",
    icon: "/media/products/mcp/plate.webp",
    image: "/media/products/mcp/plate.webp",
  },
  {
    name: "Angle",
    icon: "/media/products/mcp/angle.webp",
    image: "/media/products/mcp/angle.webp",
  },
  {
    name: "Steel Tube",
    icon: "/media/products/mcp/steel-tube.webp",
    image: "/media/products/mcp/steel-tube.webp",
  },
  {
    name: "Flats",
    icon: "/media/products/mcp/flats.webp",
    image: "/media/products/mcp/flats.webp",
  },
  {
    name: "Sheet Piling",
    icon: "/media/products/mcp/sheet-piling.webp",
    image: "/media/products/mcp/sheet-piling.webp",
  },
  {
    name: "Structural Tee",
    icon: "/media/products/mcp/structural-tee.webp",
    image: "/media/products/mcp/structural-tee.webp",
  },
  {
    name: "Wide Flange",
    icon: "/media/products/mcp/wide-flange.webp",
    image: "/media/products/mcp/wide-flange.webp",
  },
] as const;

export const about = {
  title: "About Us",
  paragraphs: [
    `The Mark Wholesale Group Holding Established 2011 And Is Privately held, “the Company” Growing as the North East Largest Vertically Integrated Industrial Metal Supply-Chain, Warehousing, Processing, & Distribution, Offering Diversified Carbon Steel Products. High Strength Steel & Low Alloy Specializing All Bar Shapes Used Primarily in Commercial Concrete Projects. The Company Has Metal Processing Facilities on Project Based needs and Ability to meet the requirements of Customers who demand on-time deliveries. Particularly Reinforced Concrete Bar. We Carry Large Stock All Sizes In NE, As Well All Related Concrete products. Company has generated impressive revenue growth and profitability in recent years solidifying itself as a highly profitable $25 million organization with forecasted revenues upwards of $33 million projected End 2018.`,
    `The Company’s Growth strategy is to continue to service its customers by not only Providing Quality Steel, But By Added Value, Total Supply Chain Deep Foundation & Concrete Superstructure Trade, SOE Foundation Slab Steel, Caisson Pile, Lagging Lumber, WF H-Pile & Pipe Steel Beams, Gr60 ~ 150 Threaded Solid & Hollow Anchoring Bars, Our Rebar Fabrication Division Serving Foundation, Super-structure High Rise Trade, In addition, Concrete related Materials. Accessories Slab bolsters and Upper Wire Chairs, Tie wire, In house Project Engineering and Coordination On customers Scope specifications.`,
  ],
  image: "/media/deep-foundation/Caisson_Threadbar_Cages.JPG",
};

export const services = {
  title: "Services",
  lead: "Our Market Trading Capacity On Various Metals",
  body: `Our Ability to leverage Risk By Mark to market On All Products By Trading all Levels Of Industrial Metals & Lumber Commodity, our subsidiaries contracts ability Leveraging Risk On Larger Project Future Contracts on All levels of Supply, We Manage our position & exposure in real-time, Take action based on price changes anywhere in the world Tightly manage counterparty credit & Keep full view control of Credit & cash flow.`,
  platformTitle: "Metal’s Market Platform",
  marketLogos: [
    { name: "Dow Jones", src: "/media/markets/logo-dow-jones.png" },
    { name: "Platts", src: "/media/markets/plattslogo.png" },
    { name: "BBC", src: "/media/markets/BBC_Logo.png" },
    { name: "London Metal Exchange", src: "/media/markets/London_Metal_Exchange_logo.png" },
    { name: "CME", src: "/media/markets/CME-Logo.png" },
    { name: "Intercontinental Exchange", src: "/media/markets/Intercontinental_Exchange_logo.png" },
    { name: "Mabux", src: "/media/markets/mabux-logo.png" },
  ],
};

export const productsDetail = {
  title: "Products",
  featuring: "Featuring Steel Products:",
  hotCarbon:
    "HOT CARBON & ALLOY STEEL SHAPES ANGLE, BEAM, CHANNEL, PLATE, FLOOR, PLATE, SHEET, PIPE, BAR, TUBE, GRATING, EXPANDED & PERFORATED METAL,",
  coated:
    "Coated Steel & Specialty Products: Epoxy coated Steel, Galvanized metals, high strength steel, threaded bar, hollow bar, wire Mesh, bar joist, Architectural metals",
  steelProducts: [
    "Structural Tee",
    "Sheet Piling",
    "Wide Flange",
    "Flats",
    "Steel Tube",
    "Angle",
    "Plate",
    "Rail Shapes",
    "Pipe Pile",
    "Channel",
    "Bars",
    "H-Pile",
  ],
  deepFoundationTitle: "Deep Foundation Products",
  deepFoundationImages: [
    "/media/deep-foundation/CAISSON_PLAIN_PIPE.JPG",
    "/media/deep-foundation/HP_Pile_Beams.JPG",
    "/media/deep-foundation/Soldier_Pile.JPG",
    "/media/deep-foundation/Drilling_Tie-Backs_MicroPiles.JPG",
    "/media/deep-foundation/MicroPile_Pipe.JPG",
    "/media/deep-foundation/Support_Of_Excavation.JPG",
    "/media/deep-foundation/Deep_Foundation_Wrakers.JPG",
    "/media/deep-foundation/Threaded_bar2.JPG",
  ],
  suppliers: [
    { name: "Nucor", src: "/media/suppliers/Nucor-Logo-PNG-Transparent.png" },
    { name: "Gerdau", src: "/media/suppliers/Gerdau_logo.png" },
    { name: "Commercial Metals Company", src: "/media/suppliers/Commercial_Metals_Company.png" },
    { name: "SDI", src: "/media/suppliers/SDI.png" },
    { name: "United States Steel", src: "/media/suppliers/united-states-steel-logo.png" },
    { name: "ArcelorMittal", src: "/media/suppliers/Arcelor_Mittal.png" },
    { name: "SAS Stressteel", src: "/media/suppliers/logo-sas-stressteel.png" },
    { name: "MMFX", src: "/media/suppliers/mmfxlogo2.png" },
    { name: "Lane", src: "/media/suppliers/LANE-Logo.png" },
    { name: "Exltube", src: "/media/suppliers/Exltube-Logo.png" },
    { name: "Vulcraft Verco Group", src: "/media/suppliers/Vulcraft-VercoGroup.png" },
  ],
};

export const featuredProjects = [
  {
    title: "54 Noll, Brooklyn NYC {Rheingold Brewery}",
    image: "/media/projects/Project1.JPG",
  },
  {
    title: "123 Meserole, Brooklyn NYC",
    image: "/media/projects/Project2.JPG",
  },
  {
    title: "Tangram Plaza, Flushing Queens NYC",
    image: "/media/projects/Project3.JPG",
  },
  {
    title: "NYC Deep Foundation",
    image: "/media/projects/Project4.JPG",
  },
  {
    title: "Brooklyn Superstructure",
    image: "/media/projects/Project5.JPG",
  },
  {
    title: "Manhattan Supply",
    image: "/media/projects/Project6.JPG",
  },
] as const;

export const completedProjects = [
  "321 Wythe Ave., Brooklyn, NY 11249",
  "26 Ann St., New York, NY 10038",
  "ESSEX SITE 6",
  "175 Delancey St., New York, NY 10002",
  "608 Franklin Ave., Brooklyn, NY 11238",
  "581 Ocean Pkwy., Brooklyn, NY 11218",
  "54 Noll St., Brooklyn, NY 11206",
  "MOXY HOTEL",
  "105-109 W 28th St., New York, NY 10001",
  "11 Stone St., New York, NY 10004",
  "801 Wyckoff Ave., Brooklyn, NY 11385",
  "1326 Ocean Ave., Brooklyn, NY 11230",
] as const;

export const galleryImages = [
  "/media/gallery/MWGallery10.JPG",
  "/media/gallery/MWGellary7.JPG",
  "/media/gallery/MWGallary1.JPG",
  "/media/gallery/MWGallery4.JPG",
  "/media/gallery/MWGallery5.JPG",
  "/media/gallery/MWGallery6.JPG",
  "/media/gallery/MWGallary2.JPG",
  "/media/gallery/MWGallary3.JPG",
  "/media/gallery/MWGallery9.JPG",
  "/media/gallery/MWGellary8.JPG",
] as const;

export const contact = {
  title: "Contact Us",
  success: "Thanks for submitting!",
  corporate: {
    title: "Corporate Office",
    lines: [
      "146 Spencer Suite 5005, Brooklyn, NY",
      "Phone: 718.387.4600",
      "Fax: 718.228.5181",
      "Mail Add: 670 Myrtle Ave #251 Bklyn NY, 11205",
    ],
  },
  primeRebar: {
    title: "Prime Rebar LLC",
    lines: ["Main office: 908.707.1234", "121B High Hill Road", "Swedesboro, NJ 08085"],
    logo: "/media/logos/primeRebar_logo.png",
  },
  subsidiariesTitle: "Our Other Subsidiaries Managed By",
  subsidiaries: [
    { name: "Matels Trading Division", logo: "/media/logos/TranLogoMW.webp" },
    { name: "TITON Grip", logo: "/media/subsidiaries/TITON_Grip.webp" },
    { name: "Halemark", logo: "/media/subsidiaries/Halemark.webp" },
    { name: "Consulting Design", logo: "/media/subsidiaries/Consulting_Design.webp" },
  ],
};
