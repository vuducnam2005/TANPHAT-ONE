// Original vector illustration: a cable-stayed bridge, drawn once on arrival.
export function BridgeIllustration() {
  return (
    <svg className="tp-bridge" viewBox="0 0 760 460" fill="none" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="bridge-water" x1="380" y1="295" x2="380" y2="460" gradientUnits="userSpaceOnUse">
          <stop stopColor="#204f65" /><stop offset="1" stopColor="#15384e" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="bridge-deck" x1="0" y1="275" x2="760" y2="295" gradientUnits="userSpaceOnUse">
          <stop stopColor="#38667a" /><stop offset=".52" stopColor="#8eafbb" /><stop offset="1" stopColor="#38667a" />
        </linearGradient>
      </defs>
      <circle cx="576" cy="122" r="57" fill="#e7bd79" fillOpacity=".07" />
      <circle cx="576" cy="122" r="33" fill="#e7bd79" fillOpacity=".12" />
      <circle cx="576" cy="122" r="17" fill="#e7bd79" fillOpacity=".65" />
      <path d="M0 266 95 221 181 242 251 209 329 248 432 223 519 251 635 212 760 249V308H0Z" fill="#20475b" />
      <path d="m0 285 115-34 109 28 97-24 121 26 143-39 175 28v47H0Z" fill="#285268" fillOpacity=".55" />
      <path d="M0 304H760V460H0Z" fill="url(#bridge-water)" />
      <g stroke="#76a0b2" strokeOpacity=".17" strokeLinecap="round">
        <path d="M44 349h108m22 0h47m272 0h174M13 385h112m27 0h96m105 0h102m99 0h160M75 422h140m42 0h49m132 0h198" />
        <path d="M88 363h213m204 0h103M35 402h54m145 0h223m194 0h86" />
      </g>
      <g stroke="#76a0b2" strokeOpacity=".22" strokeDasharray="3 7">
        <path d="M231 40v372M518 77v335M25 291h710" />
      </g>
      <g className="tp-bridge-cables" stroke="#9ec7d1" strokeWidth="1.2" strokeOpacity=".72">
        {[66, 99, 132, 165, 198, 264, 297, 330, 363, 396].map((x) => (
          <path key={x} d={`M231 85 ${x} 282`} pathLength="1" />
        ))}
        {[382, 410, 438, 466, 494, 542, 570, 598, 626, 654].map((x) => (
          <path key={x} d={`M518 123 ${x} 282`} pathLength="1" />
        ))}
      </g>
      <path d="M211 333 226 64h10l16 269h-12l-9-187-9 187Z" fill="#88a9b6" />
      <path d="m226 64 5-12 5 12-5 102Z" fill="#c5d9df" />
      <path d="m500 326 14-221h9l14 221h-11l-8-158-7 158Z" fill="#7d9da9" />
      <path d="m514 105 4-10 5 10-5 63Z" fill="#c5d9df" />
      <path d="M0 282H760v12H0Z" fill="url(#bridge-deck)" />
      <path className="tp-bridge-road" d="M0 282H760" stroke="#e7bd79" strokeWidth="2.5" pathLength="1" />
      <path d="M0 297H760" stroke="#102f43" strokeWidth="5" />
      <g fill="#597e90"><path d="M84 299h8v40h-8ZM674 299h8v40h-8Z" /></g>
      <g stroke="#9ccbd4" strokeOpacity=".75">
        <path d="M220 51h22m-11-11v22M507 93h22m-11-11v22" />
      </g>
      <g fill="#e7bd79"><circle cx="231" cy="52" r="3" /><circle cx="518" cy="95" r="3" /></g>
    </svg>
  );
}
