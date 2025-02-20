import { Grid, Stack } from '@mantine/core';

import { useMediaQuery } from '@mantine/hooks';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';
import ProfessorCard from 'components/ProfessorCard';
import { DividerTitle } from 'components';

// type HeaderProps = {
//   course: {
//     name: string;
//     description: string;
//   };
// };

const ProfessorsSection = () => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  const infoData: { fullName: string; description: string }[] = [
    {
      fullName: 'BILL DISCHINGER',
      description:
        'Adjunct professor at the University of the Pacific department of orthodontics in San Francisco, California.Private practice owner in Lake Oswego and Canby, Oregon, USA.Speaker of numerous international congresses.',
    },
    {
      fullName: 'ALFREDO RIZZO',
      description:
        'Second level university master in Damon systematics at the university of Siena.Self-employed in his own dental clinics and as a consultant.Member of the European founding group Damon Ultima.',
    },
    {
      fullName: 'TREVOR NICHOLS',
      description:
        'ORMCO key opinion leader and speaker.Master of science in orthodontics.Partner at the world-renown Frost orthodontics.',
    },
    {
      fullName: 'AMR ASKER',
      description:
        'Master of science in orthodontics in Donau university and Master of science in periodontics in Mansoura university.Author of 100 Asker’s orthodontic tips.Member of American dental association and Europe orthodontic society.',
    },
    {
      fullName: 'NASIB BALUT',
      description:
        'Past-president of the mexican board oforthodontics.Certified educator of Damon system.Author of the Book “Mini implantes como anclaje en ortodoncia”.',
    },
    {
      fullName: 'DMITRY I',
      description:
        'Experience with Damon System since 2011.Ormco Lecturer .Head orthodontic department of the dental clinic, St. Petersburg.',
    },
  ];

  return (
    <Stack gap={40}>
      <DividerTitle maw="80%">Professors</DividerTitle>

      <Grid columns={isMobile ? 1 : 2}>
        {infoData.map(({ fullName, description }, index) => (
          <Grid.Col span={1} order={index + 1}>
            <ProfessorCard description={description} fullName={fullName} url="" isMobile={isMobile} />
          </Grid.Col>
        ))}
      </Grid>
    </Stack>
  );
};

export default ProfessorsSection;
