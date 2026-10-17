const attackNames = {
  Blade: "Lame",
  Blossom: "Floraison",
  "Breathe Fire": "Souffle de feu",
  Bullet: "Projectile",
  Buzz: "Bourdonnement",
  Constrict: "Étreinte",
  Feint: "Feinte",
  Fester: "Infection",
  "Fire Ball": "Boule de feu",
  "Fire Claw": "Griffe de feu",
  Flood: "Déluge",
  Flow: "Courant",
  Gnaw: "Mordillage",
  Goad: "Provocation",
  Hammerhead: "Coup de tête",
  "Ice Claw": "Griffe de glace",
  "Leaf Stab": "Lame-feuille",
  "Lick Lash": "Coup de langue",
  "Midnight Mantle": "Manteau de minuit",
  Muddle: "Confusion",
  Mudslide: "Coulée de boue",
  "Neural Glimpse": "Aperçu neural",
  "Latent Echo": "Écho latent",
  "One-Two": "Double frappe",
  Peck: "Picore",
  "Pollen Blast": "Explosion de pollen",
  Quicksand: "Sables mouvants",
  Ram: "Charge",
  Rock: "Rocher",
  "Shadow Boxing": "Boxe de l’ombre",
  Shuriken: "Shuriken",
  "Spit Poison": "Crachat venimeux",
  Splinter: "Écharde",
  "Staff Smash": "Coup de bâton",
  Starfall: "Pluie d’étoiles",
  Stick: "Bâton",
  Sting: "Piqûre",
  Sunburst: "Éclat solaire",
  "Tail Lash": "Coup de queue",
  Thunderball: "Orbe foudroyant",
  "Wall of Steel": "Mur d’acier",
  Whirlwind: "Tourbillon",
  "Wing Tip": "Coup d’aile",
  "Zero Day": "Jour zéro",
  "Golden Ticket": "Ticket d’or",
};

export const localizeAttackName = (name) => attackNames[name] || name;

const loreBySlug = {
  rockitten: "Il utilise ses petites oreilles de pierre pour faire des câlins.",
  aardorn:
    "À sa naissance, il est déposé dans une fourmilière et doit en sortir en se frayant un chemin à coups de dents.",
  agnite:
    "Très joueur, il doit apprendre très tôt à maîtriser le feu qui l’anime.",
  tweesher:
    "Plus il fait froid, plus son bec durcit. Sous 0 °C, il devient plus dur que le diamant.",
  cardiling:
    "Personne ne s’attend à le voir cracher du feu… jusqu’à ce qu’il le fasse.",
  budaye:
    "Avec quelques miaulements et gestes encourageants, il sait convaincre tout un groupe de coopérer pour le bien commun.",
  cataspike:
    "Il apprend à se battre en observant. Livré à lui-même, il utilise sa pointe pour ramasser les déchets.",
  dollfin:
    "Chacun suit un navire de port en port afin d’explorer le monde.",
  nudiflot:
    "Lorsqu’il est attaqué, ses antennes plumeuses se détachent et déroutent son prédateur.",
  fruitera:
    "Fruitera raffole des fruits et en transporte autant que possible. Effrayé, il les laisse tomber, les ramasse tous, puis prend enfin la fuite.",
  lambert:
    "Son parent le place dans sa noix avant de l’envoyer découvrir le monde.",
  pairagrin:
    "Jeune forme de Pairagrim, c’est une créature généralement joyeuse. Elle peine à voler tant que ses deux têtes n’ont pas appris à coopérer.",
  anoleaf:
    "Il considère les plantes qui poussent près de lui comme ses frères et sœurs.",
  chenipode:
    "Il mord les lacets et les jambes de pantalon lorsqu’il veut voyager.",
  squabbit:
    "Pour faire leurs preuves, les Squabbit se battent bec et ongles au moindre prétexte.",
  vivipere:
    "Il éclot en grand nombre pendant l’été, mais le reste de son cycle de vie demeure mystérieux.",
  bursa:
    "Il juge le feu trop élémentaire et ne produit que les flammes de l’esprit.",
  dandylion:
    "Il ne donne naissance qu’à une seule portée, puis parcourt le monde pour tenter de la retrouver.",
  rockat: "Malgré son poids considérable, ses pas ne font aucun bruit.",
  aardart:
    "Il compte chaque fourmi qu’il dévore et célèbre les nombres qui lui semblent importants.",
  agnidon:
    "Il préfère marcher à quatre pattes, mais se redresse pour ouvrir une porte, renverser un arbre ou saisir un objet.",
  bamboon:
    "Il combat avec son bâton de bambou, qui lui sert aussi à garder l’équilibre.",
  cardiwing:
    "Son chant est remarquable, mais peu de gens osent adopter un oiseau chanteur explosif.",
  bigfin:
    "Tout un écosystème vit sur son dos ; il évite donc de plonger sous l’eau.",
  axolightl:
    "Sa queue éclaire les eaux profondes et indique aux poissons un abri sûr.",
  djinnbo:
    "On croit à tort qu’il s’agit d’un humain mort dans un incendie. En réalité, ce sont ses proches qui ont péri.",
  bugnin:
    "Son épée est en réalité une antenne qu’il a fait pousser, puis cassée pour cet usage.",
  propellercat:
    "S’agit-il d’une nouvelle espèce ou simplement de l’animal d’un inventeur ?",
  legko:
    "Longtemps considéré comme dépourvu de pattes, il possède en réalité des membres vestigiaux en forme de feuilles.",
  eyenemy:
    "Il se nourrit de beaux panoramas et de tout autre spectacle saisissant.",
  agnigon:
    "On le surnomme « faux dragon » : il en a l’apparence, mais descend d’une autre lignée de reptiles anciens.",
  jemuar:
    "Les gemmes de son dos dépendent de son lieu de naissance. De grands élevages de Rockitten sont installés au-dessus des filons de diamant.",
  cardinale:
    "Il voue une haine farouche aux prédateurs et leur fait la guerre, ainsi qu’à leurs petits, dès qu’il le peut.",
  moloch:
    "Il peut durcir ou assouplir sa peau selon qu’il fait face à un ami ou à un ennemi.",
  bolt:
    "La présence d’un Bolt pousse un Nut à se resserrer davantage et à produire plus d’énergie.",
  pigabyte:
    "Les scientifiques ont découvert que les meilleurs ordinateurs possèdent des implants organiques.",
  ignibus:
    "Menacé, il se réfugie dans sa carapace et se refroidit brutalement en évacuant de la vapeur. On pourrait le prendre pour un rocher.",
  allagon:
    "Les Allagon sont attirés par les reliques forgées dans les métaux laissés par leurs ancêtres et deviennent violents pour les récupérer.",
  tux:
    "À l’aise sous les climats arctiques, Tux bondit sur les proies faibles. Contre les plus robustes, il les fait glisser sur la glace pour briser leur carapace contre les rochers.",
  zunna:
    "Le joyeux Zunna aspire dans son estomac toute la nourriture qu’il peut trouver.",
};

export function localizeCard(card) {
  return {
    ...card,
    attacks: card.attacks.map((attack) => ({
      ...attack,
      name: localizeAttackName(attack.name),
    })),
    lore: loreBySlug[card.slug] || card.lore,
  };
}
