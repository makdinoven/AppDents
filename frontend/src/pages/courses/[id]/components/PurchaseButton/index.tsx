import { Button, Text } from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';
import Icon, { IconType } from 'components/Icon';
import { MOBILE_SCREEN_PX } from 'resources/app/app.constants';

const PurchaseButton = () => {
  const isMobile = useMediaQuery(`(max-width: ${MOBILE_SCREEN_PX}px)`);

  return (
    <Button
      variant="filled"
      justify="space-between"
      rightSection={<Icon type={IconType.CircleArrow} color="inherit" />}
      miw={isMobile ? 200 : 400}
      w={isMobile ? 200 : 400}
    >
      <Text size="lg" inline>
        Buy for $312{' '}
        <Text c="main.3" component="span" td="line-through">
          $19
        </Text>
      </Text>
    </Button>
  );
};

export default PurchaseButton;
