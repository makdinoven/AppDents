import { MantineColorsTuple } from '@mantine/core';

export const colors: Record<string, MantineColorsTuple> = {
  main: [
    '#E6F8F6',
    '#C2EFEA',
    '##7FDFD5CC', // Base color 80% (index 3)
    '#7FDFD5', // Base color (index 3)
    '#66CFC5',
    '#4DBFB4',
    '#37AFA4',
    '#2A9086',
    '#1C7168',
    '#0E5249',
  ],
  background: [
    '#F9FCFF',
    '#EEF9FF',
    '#EDF8FF99', // 60%
    '#EDF8FF', // Base color (index 3)
    '#C4E5FF',
    '#9ED3FF',
    '#7ABFFF',
    '#56ABFF',
    '#318FFF',
    '#1573E6',
  ],
  text: [
    '#E6F4F3',
    '#B9E0DC',
    '#8BCAC5',
    '#5CB3AD',
    '#01433DCC', // glass 80% index 4
    '#017E73',
    '#016B61',
    '#01574F',
    '#01433D', // Base color (index 8) text
    '#00322E',
  ],
  error: [
    '#FAF5F4',
    '#ECD7D1',
    '#E4BAAC',
    '#E49C85',
    '#ED7C59',
    '#FF5A26', // main: (index: 5)
    '#E64E1F',
    '#BE4D2A',
    '#9C4C32',
    '#824836',
  ],
  secondaryBlue: [
    // secondary 1
    '#E4F4F9',
    '#B8E0EC',
    '#8ACCDD',
    '#5CB8CE',
    '#2EA4BF',
    '#006D8D', // Base color (index 5)
    '#005E7A',
    '#004F68',
    '#003F56',
    '#002F45',
  ],
  secondaryGreen: [
    // secondary 2
    '#E5F6F4',
    '#B8E5DF',
    '#8AD4C9',
    '#5FC3B4',
    '#3AA49A',
    '#017F74', // Base color (index 5)
    '#016F65',
    '#015F56',
    '#014F48',
    '#003F3A',
  ],
  secondarySkyBlue: [
    // secondary 3
    '#EAF8FC',
    '#CDEDF6',
    '#B0E3F0',
    '#93D8EA',
    '#79CEE7', // Base color (index 4)
    '#5BB3CF',
    '#3D99B7',
    '#2E7D94',
    '#1E6271',
    '#0F4651',
  ],
  secondaryGray: [
    // secondary 4
    '#E8EBEB',
    '#C8D0D0',
    '#A8B5B4',
    '#889A99',
    '#687F7E',
    '#5B6968', // Base color (index 5)
    '#4E5857',
    '#404746',
    '#333736',
    '#262828',
  ],
};
