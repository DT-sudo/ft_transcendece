const base = {
  xmlns: 'http://www.w3.org/2000/svg',
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
  'aria-hidden': true,
};

function Icon({ size = 16, children, ...props }) {
  return (
    <svg {...base} width={size} height={size} {...props}>
      {children}
    </svg>
  );
}

export const ChevronDown = (props) => (
  <Icon {...props}>
    <path d="m6 9 6 6 6-6" />
  </Icon>
);

export const ChevronLeft = (props) => (
  <Icon {...props}>
    <path d="m15 18-6-6 6-6" />
  </Icon>
);

export const ChevronRight = (props) => (
  <Icon {...props}>
    <path d="m9 18 6-6-6-6" />
  </Icon>
);

export const Plus = (props) => (
  <Icon {...props}>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </Icon>
);

export const X = ({ size = 20, ...props }) => (
  <Icon size={size} {...props}>
    <line x1="18" x2="6" y1="6" y2="18" />
    <line x1="6" x2="18" y1="6" y2="18" />
  </Icon>
);

export const Trash = ({ size = 18, ...props }) => (
  <Icon size={size} {...props}>
    <path d="M3 6h18" />
    <path d="M8 6V4h8v2" />
    <path d="M19 6l-1 14H6L5 6" />
    <path d="M10 11v6" />
    <path d="M14 11v6" />
  </Icon>
);

export const MoreVertical = ({ size = 18, ...props }) => (
  <Icon size={size} {...props}>
    <circle cx="12" cy="12" r="1" />
    <circle cx="12" cy="5" r="1" />
    <circle cx="12" cy="19" r="1" />
  </Icon>
);

export const CalendarIcon = ({ size = 20, ...props }) => (
  <Icon size={size} {...props}>
    <path d="M8 7V3" />
    <path d="M16 7V3" />
    <path d="M4 11h16" />
    <path d="M4 21h16" />
    <path d="M4 7h16" />
    <path d="M4 11v10" />
  </Icon>
);

export const Search = ({ size = 18, ...props }) => (
  <Icon size={size} {...props}>
    <circle cx="11" cy="11" r="7" />
    <path d="m21 21-4.3-4.3" />
  </Icon>
);

export const BarChartIcon = ({ size = 18, ...props }) => (
  <Icon size={size} {...props}>
    <path d="M3 3v18h18" />
    <rect x="7" y="12" width="3" height="6" />
    <rect x="12" y="8" width="3" height="10" />
    <rect x="17" y="5" width="3" height="13" />
  </Icon>
);

export const Download = ({ size = 16, ...props }) => (
  <Icon size={size} {...props}>
    <path d="M12 3v12" />
    <path d="m7 10 5 5 5-5" />
    <path d="M5 21h14" />
  </Icon>
);

export const RefreshCw = ({ size = 16, ...props }) => (
  <Icon size={size} {...props}>
    <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
    <path d="M21 3v5h-5" />
    <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
    <path d="M3 21v-5h5" />
  </Icon>
);

export const ArrowUpDown = ({ size = 14, ...props }) => (
  <Icon size={size} {...props}>
    <path d="m7 15 5 5 5-5" />
    <path d="m7 9 5-5 5 5" />
  </Icon>
);

export const Bell = ({ size = 18, ...props }) => (
  <Icon size={size} {...props}>
    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
  </Icon>
);
