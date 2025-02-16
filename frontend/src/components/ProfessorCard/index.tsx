import { Avatar, Group, Title, Text, Stack } from '@mantine/core';

type ProfessorCardProps = {
  url?: string;
  description: string;
  fullName: string;
};

const ProfessorCard = ({ url, description, fullName }: ProfessorCardProps) => (
  <Group wrap="nowrap">
    <Avatar variant="filled" radius="100%" c="secondaryBlue.5" src={url} size={190} />

    <Stack>
      <Title order={4} c="text.8">
        {fullName}
      </Title>
      <Text c="text.8" size="md">
        {description}
      </Text>
    </Stack>
  </Group>
);

export default ProfessorCard;
